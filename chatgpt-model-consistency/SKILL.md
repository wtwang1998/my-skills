---
name: chatgpt-model-consistency
description: Inspect the current ChatGPT web app's conversation request and streamed server metadata to determine whether the requested model matches the server-selected model. Use for browser-side ChatGPT validation, not API model selection or general ChatGPT questions.
---

# ChatGPT Model Consistency

Use this skill when the user wants to verify which model the current ChatGPT
web page requested and which model the server actually annotated in the
response.

## Scope and safety

- Work only in the current signed-in `https://chatgpt.com/` browser session.
  Do not replace this check with a direct API request, web search, or another
  ChatGPT client.
- Reuse the current ChatGPT tab. If no such tab exists, open exactly one
  `https://chatgpt.com/` tab and wait for a usable composer. Do not duplicate
  an existing tab. If login, a CAPTCHA, or a browser permission prompt is
  required, stop and ask the user to handle it; never automate it.
- The provided checker observes the page's existing `fetch`, XHR, and beacon
  traffic locally. It does not need cookies, headers, access tokens, request
  bodies, response bodies, or raw conversation text in the result. Never copy
  or report those values.
- Send exactly one harmless, non-sensitive test message, and only after the
  checker is visibly running. Sending the message is an external side effect:
  prepare everything first, then ask for confirmation immediately before the
  send action. A prior generic request to perform the check does not replace
  this action-time confirmation.
- Treat `server_ste_metadata.model_slug` as the primary server-side evidence.
  Assistant metadata and the DOM attribute are corroboration only and must
  not override a missing or conflicting server annotation.

## Workflow

### 1. Select and prepare one tab

1. Focus the existing user-mentioned or selected `chatgpt.com` tab when one is
   available. Otherwise create one tab at the exact site URL. Confirm that the
   page is usable and signed in before proceeding.
2. If the environment cleans up temporary tabs when a turn pauses, preserve
   the tab for handoff before asking for confirmation (for example, use the
   browser's handoff/persistence marker when available). After a new turn,
   re-observe the tab and its composer; never reuse stale element indexes or
   a stale tab handle.

### 2. Install the checker exactly once

1. If `ChatGPT Route Checker v5` is already running, reuse its existing panel
   and do not inject a second copy.
2. Load the exact, unchanged contents of
   [`assets/chatgpt-route-checker-v5.js`](assets/chatgpt-route-checker-v5.js)
   into the same page context. Prefer a browser-provided page CDP/runtime
   evaluation path when available: read the local asset and pass its contents
   unchanged to the page. This is local instrumentation, not a direct API
   request. Do not manually transcribe, shorten, reconstruct, or paste a
   partial script.
3. If page CDP/runtime evaluation is unavailable, open the page's DevTools
   Console and paste the exact asset contents there. If the browser displays
   its normal console-paste protection, the user must type the required
   confirmation (commonly `allow pasting`) themselves before the paste. Never
   paste the script into the ChatGPT composer.
4. Verify that the page shows `ChatGPT Route Checker v5` and that it is waiting
   for a new message. If the panel or start signal is absent, stop and do not
   send a test message.

### 3. Confirm and send one test message

1. Ask for confirmation immediately before sending the one harmless test
   message. If the user declines or does not confirm, stop and report that no
   measurement was made.
2. After confirmation, re-observe the composer and its focus, then send one
   harmless message such as `请回复：模型一致性测试。` Do not send another
   test turn, retry blindly, or use a suggested prompt.

### 4. Collect the stable panel result

1. Wait for the assistant response and poll the checker panel every few
   seconds, for at most about 30 seconds. Stop when the response is visibly
   complete, the two primary fields are present, and one additional check
   shows no panel change. Do not wait indefinitely for optional fields.
2. Read only these fields from the panel:

   - `request.model`
   - `server_ste_metadata.model_slug` (primary)
   - `assistant metadata.model_slug`
   - `resolved_model_slug`
   - `requested_model_experience`
   - `DOM data-message-model-slug`

3. If either primary field is still absent after the timeout, report
   **无法判定** and identify the missing field. Do not send a second message.
   Treat placeholders such as `搜索中…` as missing, not as model values.

## Decision rules

Let `request.model` be the requested value and
`server_ste_metadata.model_slug` be the server value.

- Both present and exactly equal: **一致（精确 slug 相同）**.
- Both present but different, while their `gpt-M-N` family prefixes match:
  **同一模型系列，但内部 slug 不同**. Do not call this an exact match.
- Both present and their `gpt-M-N` families differ: **不一致**.
- Either primary value is missing after the response: **无法判定**. Do not
  infer a match from only assistant metadata, `resolved_model_slug`, or the
  DOM label.
- A missing conversation request is an instrumentation failure, not evidence
  of a model mismatch.
- If auxiliary fields disagree with the primary server value, report the
  disagreement as a note rather than silently changing the verdict.

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
After recording the result, remove the in-page instrumentation by reloading
an agent-created tab or closing it when safe. Do not reload a user-owned tab
while it contains unsent content; in that case, leave it alone and mention
that cleanup was skipped.
