---
name: chatgpt-model-consistency
description: Inspect the current ChatGPT web app's conversation request and streamed server metadata to determine whether the requested model matches the server-selected model. Use for browser-side ChatGPT validation, not API model selection or general ChatGPT questions.
---

# ChatGPT Model Consistency

Use this skill when the user wants to verify which model the current ChatGPT
web page requested and which model the server actually annotated in the
response.

## Scope and safety

- Work only in the user-visible `https://chatgpt.com/` page and its current
  signed-in browser session. Use the available browser/computer-use controls;
  do not replace this check with a direct API request or web search.
- The provided checker observes the page's existing `fetch`, XHR, and beacon
  traffic locally. It does not need cookies, headers, access tokens, or raw
  conversation text in the result. Never copy or report those values.
- Send one harmless, non-sensitive test message. Do not put credentials,
  private data, or secrets in the test message.
- Treat `server_ste_metadata.model_slug` as the primary server-side evidence.
  Assistant metadata and the DOM attribute are corroboration only and must
  not override a missing or conflicting server annotation.

## Workflow

1. Open or focus `https://chatgpt.com/` and wait until the conversation page is
   usable. If the checker is already running, reuse its panel; do not inject a
   second copy.
2. Open the page's DevTools Console. Read and paste the exact payload from
   [`assets/chatgpt-route-checker-v5.js`](assets/chatgpt-route-checker-v5.js),
   then execute it in the page context. If the browser shows its normal
   console-paste protection, the user must type the browser's required
   confirmation (commonly `allow pasting`) themselves before pasting code.
   Confirm the console reports that `ChatGPT Route Checker v5` started.
3. In the same ChatGPT tab, send exactly one new harmless test message, for
   example `请回复：模型一致性测试。` Wait for the assistant response and for
   the lower-right checker panel to stop updating. Allow a reasonable wait for
   the response; do not send another test turn while collecting evidence.
4. Read only the model fields shown in the panel:

   - `request.model`
   - `server_ste_metadata.model_slug` (primary)
   - `assistant metadata.model_slug`
   - `resolved_model_slug`
   - `requested_model_experience`
   - `DOM data-message-model-slug`

5. Produce a concise Chinese result using the decision rules below. Include
   the exact observed model strings and distinguish an exact match from a
   same-family match.

## Decision rules

Let `request.model` be the requested value and
`server_ste_metadata.model_slug` be the server value.

- Both present and exactly equal: **一致（精确 slug 相同）**.
- Both present but different, while their `gpt-M-N` family prefixes match:
  **同一模型系列，但内部 slug 不同**. Do not call this an exact match.
- Both present and their families differ: **不一致**.
- Either value is missing after the response: **无法判定**. Do not infer a
  match from only assistant metadata, `resolved_model_slug`, or the DOM label.
- If the panel says it is still waiting for request or server metadata, keep
  waiting within the reasonable timeout; then report **无法判定** and state
  which value was missing.

If auxiliary fields disagree with the primary server value, report the
disagreement as a note rather than silently changing the verdict. A missing
conversation request is an instrumentation failure, not evidence of a model
mismatch.

## Result format

Return:

```text
检测结果：一致（精确 slug 相同）/同系列但 slug 不同/不一致/无法判定
请求模型 request.model：<value or 未捕获>
服务端模型 server_ste_metadata.model_slug：<value or 未捕获>
辅助字段：assistant metadata=<...>；resolved=<...>；experience=<...>；DOM=<...>
说明：<必要的等待、字段冲突或 instrumentation 限制>
```

Use `未捕获` for absent values. Do not include request bodies, response
bodies, cookies, authorization data, or user message content in the report.
Refreshing the page removes the in-page instrumentation when the check is
finished.
