"""Fill the supported weekly-report template after preview approval.

Read the confirmed report JSON from stdin; see weekly-report/SKILL.md for its
fields. The helper writes no intermediate content files and only overwrites an
existing output file when the caller explicitly passes --overwrite.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

try:
    from docx import Document
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    from lxml import etree
except ImportError:
    print(
        "错误：当前 Python 环境缺少 python-docx 或 lxml；请切换到已配置这些依赖的运行时，不要自动安装。",
        file=sys.stderr,
    )
    raise SystemExit(2)


class ReportError(Exception):
    """A safe, user-actionable input or template error."""


DAILY_HEADERS = ["时间", "工作地点", "项目", "主要工作内容", "产出/结果", "耗时（h）"]
PLAN_HEADERS = ["时间", "项目", "关联中心", "工作事项", "预计耗时", "优先级"]
CENT_TO_CENT = Decimal("0.01")
WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WORD_TAG = f"{{{WORD_NS}}}"


def normalized(value: str) -> str:
    return "".join(value.split())


def required_text(mapping: dict[str, Any], key: str, *, allow_empty: bool = False) -> str:
    value = mapping.get(key)
    if not isinstance(value, str):
        raise ReportError(f"字段 {key} 必须是文本。")
    if "\n" in value or "\r" in value:
        raise ReportError(f"字段 {key} 不能包含换行；请拆分为多个列表项。")
    value = value.strip()
    if not value and not allow_empty:
        raise ReportError(f"字段 {key} 不能为空。")
    return value


def required_list(payload: dict[str, Any], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list) or not values:
        raise ReportError(f"字段 {key} 必须是至少含一项的文本列表；无内容时请明确填写“无”。")
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
            raise ReportError(f"字段 {key} 含空白或非文本项。")
        result.append(value.strip())
    return result


def decimal_hours(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ReportError(f"字段 {field} 必须是非负工时数字。")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise ReportError(f"字段 {field} 必须是非负工时数字。") from None
    if not number.is_finite() or number < 0:
        raise ReportError(f"字段 {field} 必须是有限的非负工时数字。")
    try:
        return number.quantize(CENT_TO_CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ReportError(f"字段 {field} 超出可处理范围。") from None


def format_hours(value: Decimal) -> str:
    return f"{value.quantize(CENT_TO_CENT, rounding=ROUND_HALF_UP):.2f}"


def run_format_signature(run: Any, label: str) -> tuple[str | None, str | None]:
    allowed_children = {qn("w:rPr"), qn("w:t")}
    if any(child.tag not in allowed_children for child in run._r):
        raise ReportError(f"模板栏目含不受支持的文字对象：{label}")

    style_id = run.style.style_id if run.style is not None else None
    properties = deepcopy(run._r.rPr)
    if properties is None:
        return style_id, None

    # This Chinese report template splits runs for Word's script-selection hints
    # and complex-script fallbacks. Compare the visible formatting while ignoring
    # those properties; font, size, color, emphasis, and character styles remain
    # part of the signature and must match before text runs are consolidated.
    fonts = properties.find(qn("w:rFonts"))
    if fonts is not None:
        fonts.attrib.pop(qn("w:hint"), None)
        fonts.attrib.pop(qn("w:cs"), None)
    complex_script_size = properties.find(qn("w:szCs"))
    if complex_script_size is not None:
        properties.remove(complex_script_size)
    return style_id, str(properties.xml)


def require_uniform_run_format(runs: list[Any], label: str) -> None:
    if not runs:
        raise ReportError(f"模板栏目缺少可复用的文字格式：{label}")
    first_signature = run_format_signature(runs[0], label)
    if any(run_format_signature(run, label) != first_signature for run in runs[1:]):
        raise ReportError(f"模板栏目包含混合文字格式，已停止以免破坏格式：{label}")


def paragraph_by_label(document: Any, label: str) -> Any:
    target = normalized(label)
    for paragraph in document.paragraphs:
        if normalized(paragraph.text).startswith(target):
            return paragraph
    raise ReportError(f"模板缺少栏目：{label}")


def paragraph_by_heading(document: Any, heading: str) -> Any:
    target = normalized(heading)
    for paragraph in document.paragraphs:
        if normalized(paragraph.text) == target:
            return paragraph
    raise ReportError(f"模板缺少章节：{heading}")


def set_after_label(paragraph: Any, label: str, value: str) -> None:
    runs = paragraph.runs
    if not runs or not "".join(run.text for run in runs).startswith(label):
        raise ReportError(f"模板栏目格式不受支持：{label}")

    consumed = 0
    label_end = len(label)
    split_index = None
    for index, run in enumerate(runs):
        consumed += len(run.text)
        if consumed == label_end:
            split_index = index
            break
        if consumed > label_end:
            raise ReportError(f"模板栏目文字与格式边界不匹配：{label}")
    if split_index is None or split_index + 1 >= len(runs):
        raise ReportError(f"模板栏目缺少可替换内容：{label}")

    value_runs = runs[split_index + 1 :]
    require_uniform_run_format(value_runs, label)
    value_run = value_runs[0]
    value_run.text = value
    for run in value_runs[1:]:
        run._element.getparent().remove(run._element)


def set_paragraph_text(paragraph: Any, value: str) -> None:
    runs = paragraph.runs
    require_uniform_run_format(runs, "正文段落")
    runs[0].text = value
    for run in runs[1:]:
        run._element.getparent().remove(run._element)


def section_body(
    document: Any,
    start_heading: str,
    end_heading: str,
    values: list[str],
    *,
    remove_end_heading: bool = False,
) -> None:
    paragraphs = document.paragraphs
    start = next((i for i, p in enumerate(paragraphs) if normalized(p.text) == normalized(start_heading)), None)
    if start is None:
        raise ReportError(f"模板缺少章节：{start_heading}")

    end = next(
        (i for i, p in enumerate(paragraphs) if i > start and normalized(p.text) == normalized(end_heading)),
        None,
    )
    if end is None:
        raise ReportError(f"模板章节顺序不受支持：{end_heading}")
    boundary = paragraphs[end]._p
    if remove_end_heading and any(paragraph.text.strip() for paragraph in paragraphs[end + 1 :]):
        raise ReportError(f"模板栏目 {start_heading} 后存在未识别的正文；已停止以免误删内容。")

    body = paragraphs[start + 1 : end]
    content = [paragraph for paragraph in body if paragraph.text.strip()]
    if not content:
        raise ReportError(f"模板章节缺少可复用的正文格式：{start_heading}")

    first_content = body.index(content[0])
    last_content = body.index(content[-1])
    if any(not paragraph.text.strip() for paragraph in body[first_content : last_content + 1]):
        raise ReportError(f"模板章节正文中存在无法保留的空白段落：{start_heading}")

    sample = deepcopy(content[0]._p)
    parent = content[0]._p.getparent()
    leading_blank = body[:first_content]
    trailing_blank = body[last_content + 1 :]
    for paragraph in content:
        parent.remove(paragraph._p)

    insertion_boundary = trailing_blank[0]._p if trailing_blank else boundary
    for value in values:
        element = deepcopy(sample)
        insertion_boundary.addprevious(element)
        paragraph = Paragraph(element, document._body)
        set_paragraph_text(paragraph, value)

    if remove_end_heading:
        boundary.getparent().remove(boundary)


def validate_table(table: Any, expected_headers: list[str], label: str) -> None:
    if not table.rows or len(table.columns) != len(expected_headers):
        raise ReportError(f"模板中的{label}表列数不匹配。")
    actual = [normalized(cell.text) for cell in table.rows[0].cells]
    expected = [normalized(header) for header in expected_headers]
    if actual != expected:
        raise ReportError(f"模板中的{label}表表头不匹配；已停止以免误填。")
    if len(table.rows) < 2:
        raise ReportError(f"模板中的{label}表缺少可复用的正文行格式。")
    if any(len(cell.paragraphs) != 1 for cell in table.rows[1].cells):
        raise ReportError(f"模板中的{label}表正文单元格结构不受支持。")


def replace_table_rows(table: Any, entries: list[dict[str, str]], columns: list[str]) -> None:
    sample = deepcopy(table.rows[1]._tr)
    for row in list(table.rows[1:]):
        table._tbl.remove(row._tr)

    for entry in entries:
        row_element = deepcopy(sample)
        table._tbl.append(row_element)
        row = table.rows[-1]
        for cell, key in zip(row.cells, columns, strict=True):
            if len(cell.paragraphs) != 1:
                raise ReportError("模板正文行结构发生变化；已停止以免误改格式。")
            set_paragraph_text(cell.paragraphs[0], entry[key])


def set_all_text_black(docx_path: Path) -> None:
    """Set direct black on every WordprocessingML run in the saved package."""
    staging_fd, staging_name = tempfile.mkstemp(
        prefix=f".{docx_path.stem}.black.", suffix=".tmp.docx", dir=docx_path.parent
    )
    os.close(staging_fd)
    staging_path = Path(staging_name)
    try:
        with zipfile.ZipFile(docx_path, "r") as source, zipfile.ZipFile(
            staging_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as target:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                    try:
                        parser = etree.XMLParser(resolve_entities=False, no_network=True)
                        root = etree.fromstring(data, parser=parser)
                    except etree.XMLSyntaxError:
                        raise ReportError(
                            f"DOCX 中的 Word XML 无法解析：{item.filename}"
                        ) from None
                    changed = False
                    for color in root.iter(f"{WORD_TAG}color"):
                        color.set(f"{WORD_TAG}val", "000000")
                        for attribute in ("themeColor", "themeTint", "themeShade"):
                            color.attrib.pop(f"{WORD_TAG}{attribute}", None)
                        changed = True
                    for run in root.iter(f"{WORD_TAG}r"):
                        properties = run.find(f"{WORD_TAG}rPr")
                        if properties is None:
                            properties = etree.Element(f"{WORD_TAG}rPr")
                            run.insert(0, properties)
                        color = properties.find(f"{WORD_TAG}color")
                        if color is None:
                            color = etree.Element(f"{WORD_TAG}color")
                            properties.insert(0, color)
                        color.set(f"{WORD_TAG}val", "000000")
                        for attribute in ("themeColor", "themeTint", "themeShade"):
                            color.attrib.pop(f"{WORD_TAG}{attribute}", None)
                        changed = True
                    if changed:
                        data = etree.tostring(
                            root,
                            encoding="UTF-8",
                            xml_declaration=True,
                            standalone=True,
                        )
                target.writestr(item, data)
        os.replace(staging_path, docx_path)
    except Exception:
        if staging_path.exists():
            staging_path.unlink()
        raise


def validate_entries(payload: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]], Decimal]:
    raw_daily = payload.get("daily_records")
    if not isinstance(raw_daily, list) or not raw_daily:
        raise ReportError("daily_records 必须至少包含一条当周登记记录。")

    daily = []
    summed_hours = Decimal("0.00")
    for index, raw in enumerate(raw_daily, start=1):
        if not isinstance(raw, dict):
            raise ReportError("daily_records 中存在无效记录。")
        hours = decimal_hours(raw.get("hours"), f"daily_records[{index}].hours")
        non_work = raw.get("non_work")
        if not isinstance(non_work, bool):
            raise ReportError(f"daily_records[{index}].non_work 必须明确标记是否为无工作记录。")
        result = required_text(raw, "result", allow_empty=non_work)
        if non_work and result not in {"", "—"}:
            raise ReportError(f"daily_records[{index}] 是无工作记录，产出/结果只能留空或写“—”。")
        summed_hours += hours
        daily.append(
            {
                "date": required_text(raw, "date"),
                "workplace": required_text(raw, "workplace"),
                "project": required_text(raw, "project"),
                "work_content": required_text(raw, "work_content"),
                "result": result,
                "hours": format_hours(hours),
            }
        )

    total = decimal_hours(payload.get("total_hours"), "total_hours")
    if summed_hours != total:
        raise ReportError("daily_records 工时合计与 total_hours 不一致；请先核对截图数据。")

    raw_plan = payload.get("next_week_plan")
    if not isinstance(raw_plan, list) or not raw_plan:
        raise ReportError("next_week_plan 必须至少包含一项；确认无计划时也应提供明确的“无”行。")
    plan = []
    for raw in raw_plan:
        if not isinstance(raw, dict):
            raise ReportError("next_week_plan 中存在无效记录。")
        plan.append(
            {
                "date": required_text(raw, "date"),
                "project": required_text(raw, "project"),
                "related_center": required_text(raw, "related_center"),
                "work_item": required_text(raw, "work_item"),
                "estimated_hours": required_text(raw, "estimated_hours"),
                "priority": required_text(raw, "priority"),
            }
        )
    return daily, plan, total


def build_report(
    template: Path,
    output: Path,
    payload: dict[str, Any],
    *,
    overwrite: bool = False,
) -> Path:
    if payload.get("preview_confirmed") is not True:
        raise ReportError("只有用户确认预览后才能生成 DOCX。")

    template = template.expanduser().resolve()
    output = output.expanduser().resolve()
    if not template.is_file() or template.suffix.lower() != ".docx":
        raise ReportError("模板路径必须指向可读的 DOCX 文件。")
    if output == template:
        raise ReportError("输出路径不能与模板相同。")
    if output.suffix.lower() != ".docx" or not output.parent.is_dir():
        raise ReportError("输出路径必须是已存在目录中的 DOCX 文件路径。")
    if output.exists() and not overwrite:
        raise ReportError("输出文件已存在；请指定一个新文件名，原文件未覆盖。")

    identity = payload.get("identity")
    if not isinstance(identity, dict):
        raise ReportError("identity 必须包含姓名、岗位、团队和负责人。")
    identity_values = {
        "姓名/岗位：": f"{required_text(identity, 'name')} / {required_text(identity, 'position')}",
        "所属团队/line manager：": f"{required_text(identity, 'team')} / {required_text(identity, 'manager')}",
    }
    report_period = required_text(payload, "report_period")
    travel_summary = required_text(payload, "travel_summary")
    summary_text = {
        "本周合计工时：": None,
        "本周出差天数：": travel_summary,
    }
    core_outputs = required_list(payload, "core_outputs")
    plan_variances = required_list(payload, "plan_variances")
    difficulties = required_list(payload, "difficulties_support")
    feedback = required_list(payload, "feedback_items")
    daily, plan, total = validate_entries(payload)
    summary_text["本周合计工时："] = f"{format_hours(total)}h"

    try:
        document = Document(template)
    except Exception:
        raise ReportError("无法读取模板 DOCX；请确认文件未损坏或加密。") from None

    if len(document.tables) != 2:
        raise ReportError("当前模板应包含日记录表和下周计划表两张表；已停止以免误填。")
    validate_table(document.tables[0], DAILY_HEADERS, "日记录")
    validate_table(document.tables[1], PLAN_HEADERS, "下周计划")

    # Check every required anchor before modifying the in-memory document.
    paragraph_by_label(document, "报告周期：")
    paragraph_by_label(document, "姓名/岗位：")
    paragraph_by_label(document, "所属团队/line manager：")
    paragraph_by_label(document, "本周合计工时：")
    paragraph_by_label(document, "本周出差天数：")
    for heading in (
        "1. 本周核心产出",
        "2. 计划与实际偏差",
        "3. 个人遇到的困难与所需支持",
        "三、下周个人工作计划",
        "四、其他需反馈事项",
    ):
        paragraph_by_heading(document, heading)

    for label, value in (("报告周期：", report_period), *identity_values.items(), *summary_text.items()):
        set_after_label(paragraph_by_label(document, label), label, value)

    for label in ("姓名/岗位：", "所属团队/line manager："):
        paragraph = paragraph_by_label(document, label)
        if re.search(r"\[[^\]]+\]|20XX|X月X日", paragraph.text):
            raise ReportError(f"身份栏目仍含模板占位符：{label}")

    section_body(document, "1. 本周核心产出", "2. 计划与实际偏差", core_outputs)
    section_body(document, "2. 计划与实际偏差", "3. 个人遇到的困难与所需支持", plan_variances)
    section_body(
        document,
        "3. 个人遇到的困难与所需支持",
        "三、下周个人工作计划",
        difficulties,
    )
    section_body(document, "四、其他需反馈事项", "……", feedback, remove_end_heading=True)

    replace_table_rows(
        document.tables[0],
        daily,
        ["date", "workplace", "project", "work_content", "result", "hours"],
    )
    replace_table_rows(
        document.tables[1],
        plan,
        ["date", "project", "related_center", "work_item", "estimated_hours", "priority"],
    )

    temp_path: Path | None = None
    try:
        file_descriptor, temp_name = tempfile.mkstemp(
            prefix=f".{output.stem}.", suffix=".tmp.docx", dir=output.parent
        )
        os.close(file_descriptor)
        temp_path = Path(temp_name)
        document.save(temp_path)
        set_all_text_black(temp_path)
        if overwrite:
            os.replace(temp_path, output)
            temp_path = None
        elif os.name == "nt":
            # On Windows, rename within the same directory is atomic and fails
            # if another process created the destination after the first check.
            os.rename(temp_path, output)
            temp_path = None
        else:
            # POSIX rename replaces an existing destination; hard-link creation
            # publishes atomically without replacing a competing file.
            os.link(temp_path, output)
            try:
                temp_path.unlink()
                temp_path = None
            except OSError:
                pass
    except FileExistsError:
        raise ReportError("输出文件已存在；请指定一个新文件名，原文件未覆盖。") from None
    except OSError:
        raise ReportError("保存 DOCX 失败；请确认输出目录可写且目标文件未被占用。") from None
    finally:
        if temp_path is not None and temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="将已确认的周报内容写入受支持的 DOCX 模板。")
    parser.add_argument("--template", required=True, type=Path, help="本次用户提供的 DOCX 模板")
    parser.add_argument("--output", required=True, type=Path, help="DOCX 输出路径")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="仅在用户明确授权覆盖该目标文件时使用；默认拒绝覆盖",
    )
    args = parser.parse_args()

    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        if not isinstance(payload, dict):
            raise ReportError("标准输入必须是 JSON 对象。")
        output = build_report(args.template, args.output, payload, overwrite=args.overwrite)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print("错误：标准输入必须是 UTF-8 编码的有效 JSON。", file=sys.stderr)
        return 2
    except ReportError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
