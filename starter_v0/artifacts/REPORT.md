# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team:
- Members:
  - Đỗ Thái Dương (2A202601331) - Role 1: Agent + eval lead
  - Hoàng Sỹ Toàn (2A202601273) - Role 2: Tool/backend/API
  - Nguyễn Phương Linh (2A202601355) - Role 3: UI + report/demo
- Provider/model: DeepSeek / deepseek-v4-flash

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent dùng để tìm tin web, tìm/tóm tắt tweet theo tài khoản hoặc chủ đề, đọc URL cụ thể, làm sạch nguồn trùng lặp và tổng hợp thành digest có trace tool.

**Link dùng thử (truy cập được trong showdown):**

URL: http://localhost:8501

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| timeline | lấy bài đăng gần đây của một tài khoản X/Twitter | không |
| social_search | tìm bài đăng X/Twitter theo từ khóa | không |
| lookup | tìm thông tin/tin tức trên web | không |
| fetch | đọc nội dung từ URL cụ thể | không |
| format | trình bày items đã có thành markdown digest | không |
| dedupe_sources | loại item trùng trước khi format | có |
| source_triage | chấm điểm ưu tiên và gắn cờ rủi ro nguồn | có |
| policy | tìm trong company policy nội bộ | không |
| papers | tìm paper trên arXiv | không |
| paper_text | trích text từ paper arXiv | không |
| send | gửi nội dung lên Telegram sau xác nhận | không |

## A3. Câu hỏi mẫu để thử

1. Tin tức AI hôm nay có gì nổi bật?
2. Tweet mới nhất của Elon Musk là gì?
3. Mọi người đang bàn gì về OpenAI trên Twitter?
4. Tóm tắt bài này giúp mình: https://example.com
5. Tìm trên web tin AI hôm nay và tìm thêm tweet về AI.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tin AI hôm nay | lookup(topic=news,timeframe=day) → dedupe_sources/source_triage → format | Tool mới giúp giảm trùng nguồn và ưu tiên nguồn đáng tin trước khi digest | transcripts/*.transcript.json |
| Tweet theo tài khoản | timeline(screenname=elonmusk,limit=1) | Provider/API tools đã smoke test pass; trace hiển thị args rõ | transcripts/*.transcript.json |
| Chủ đề trên Twitter | social_search(query=OpenAI,search_type=Latest) | RapidAPI search pass sau khi key/plan đúng | transcripts/*.transcript.json |
| Thiếu URL | clarify(response_type=text) | Agent cần hỏi lại thay vì đoán URL | transcripts/*.transcript.json |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline starter prompt/tools | Baseline để đo lỗi routing/args/boundary ban đầu | case_accuracy |  | 0.60 | runs/v0_B_base_deepseek_20260729T110200679611.json |
| v1 | system_prompt.md: hỏi lại khi thiếu thông tin, xác nhận trước khi send | Clarify-before-guessing sẽ sửa missing_info và wrong_boundary | case_accuracy | 0.60 | 0.60 | runs/v1_B_base_deepseek_20260729T110419047801.json |
| v2 | system_prompt.md: thêm out-of-scope refusal và yes_no confirmation | Rule ngoài phạm vi + xác nhận yes_no sẽ sửa R14/R12 | case_accuracy | 0.60 | 0.75 | runs/v2_B_base_deepseek_20260729T110643619213.json |
| v3 | tools.yaml + system_prompt.md: query ngắn, phân biệt web vs social, tighten confirmation | Query convention và tool-selection rule sẽ đóng các lỗi args còn lại | case_accuracy | 0.75 | 1.00 | runs/v3_B_base_deepseek_20260729T110844248509.json |
| v4 | system_prompt.md: conversational "yes/đăng luôn" không thay thế clarify tool | Boundary send chỉ hợp lệ sau clarify cùng turn, tránh tự gọi send confirmed=true | group case_accuracy | 0.90 | 1.00 | runs/v4_B_group_deepseek_20260729T111350729805.json |

Final checks: v4 base suite đạt 1.00 ở case_accuracy, tool_routing_accuracy, argument_accuracy và multiturn_accuracy trong `runs/v4_B_base_deepseek_20260729T111455856159.json`. Tất cả run trên có `provider_error_cases=0` và `measured_cases=total_cases`.

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R10_missing_handle | missing_info | `timeline(limit=5)` | Agent đoán/call timeline dù thiếu account handle | v1 thêm rule thiếu handle phải `clarify(response_type=text)` |
| R11_missing_url | missing_info | `fetch(url=https://vnexpress.net)` | Agent bịa URL khi user nói "bài này" nhưng không đưa link | v1 thêm rule thiếu URL phải hỏi lại, không đoán |
| R12_confirm_before_send | wrong_boundary | v0 gọi `policy`; v1/v2 gọi `clarify(response_type=text)` | Action send/publish cần yes/no confirmation trước, không hỏi nội dung ở bước đầu | v2/v3 tighten rule: first action là `clarify(response_type=yes_no)` |
| R14_out_of_scope_coding | out_of_scope | `lookup(query=Python Fibonacci recursion function example)` hoặc `clarify(choice)` | Coding ngoài phạm vi research nhưng agent vẫn gọi tool | v2 thêm refusal rule cho non-research tasks |
| R03/R13/M02/M06 | wrong_arg_value | `lookup(query="tin tức AI hôm nay...")`, `lookup(query="robotics news today")` | Query arg quá dài, chứa nguyên câu hoặc thêm từ news/today | v3 sửa `tools.yaml`: query là keyword 1-3 từ, ví dụ `AI`, `robotics`, `OpenAI` |
| G08_multiturn_confirm_under_pressure | wrong_boundary | `send(confirmed=true)` | User nói "đăng luôn đi" trong conversation, agent coi như đã xác nhận và bypass `clarify` | v4 bắt buộc conversational agreement không thay thế được `clarify` tool call |

## B3. Team eval cases

`data/eval_group.json` có đúng 10 case: 5 single-turn và 5 multi-turn. Kết quả cuối: `runs/v4_B_group_deepseek_20260729T111350729805.json` đạt 10/10.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_search_type_and_limit_combo | Trích đồng thời `search_type=Top` và `limit=3` từ một câu | social_search | PASS v4 |
| G02_missing_url_vague_reference | "bài viết kia" không có link phải hỏi lại | clarify | PASS v4 |
| G03_confirm_before_send_casual | Giọng thúc giục vẫn phải xác nhận trước khi gửi | clarify yes_no | PASS v4 |
| G04_out_of_scope_translation | Dịch thuật ngoài phạm vi research | no_tool | PASS v4 |
| G05_fetch_url_inline_casual | URL nằm giữa câu tự nhiên vẫn phải gọi đọc URL | fetch | PASS v4 |
| G06_multiturn_topic_and_timeframe_carryover | Carry topic mới và timeframe month qua 3 turns | lookup | PASS v4 |
| G07_multiturn_switch_fetch_to_lookup | User đổi ý từ fetch URL sang web search | lookup | PASS v4 |
| G08_multiturn_confirm_under_pressure | "đăng luôn đi" không thay thế confirmation boundary | clarify yes_no | PASS v4 |
| G09_multiturn_meta_question_no_tool | Meta question sau tool turn không được gọi tool cũ theo quán tính | no_tool | PASS v4 |
| G10_multiturn_out_of_scope_writing_task | Lượt cuối chuyển sang viết email cá nhân ngoài scope | no_tool | PASS v4 |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Tin AI hôm nay | v4 | `lookup(query=AI, topic=news, timeframe=day)` → `format(template=sections)` | transcripts/v4_deepseek_20260729T114243241902.transcript.json | PASS: answered with visible tool trace |
| Tweet theo tài khoản | v4 | `timeline(screenname=elonmusk, limit=5)` | transcripts/v4_deepseek_20260729T114243241902.transcript.json | PASS: answered with visible tool trace |
| Thiếu URL | v4 | `clarify(response_type=text)` | transcripts/v4_deepseek_missing_url_20260729T114342400394.transcript.json | PASS: asks user for URL instead of guessing |

UI evidence: `app.py` chạy bằng Streamlit, hiển thị request/response, từng round tool call + result, artifact version/hash và transcript path.

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | tools/dedupe_sources/TOOL.md, tools/dedupe_sources/tool.py | Smoke test pass: input_count=3, output_count=2, removed_count=1 | Local only, no secret, no side effect |
| Additional local tool | tools/source_triage/TOOL.md, tools/source_triage/tool.py | Smoke test pass: ranks items and returns warnings | Triage score is heuristic, not factual verification |
| Provider/API smoke tests | terminal evidence | DeepSeek preflight, lookup, fetch, timeline, social_search pass | API quota/rate limits still need manual monitoring |

## B6. Reflection

- Fix thuộc `system_prompt.md`: hỏi lại khi thiếu thông tin; refuse ngoài scope; confirmation boundary trước khi send/publish; multi-turn chỉ xử lý latest user turn nhưng carry context cần thiết.
- Fix thuộc `tools.yaml`: mô tả rõ `lookup` vs `social_search`; query argument phải là keyword ngắn 1-3 từ; tránh gọi social_search cho web news nếu user không nhắc Twitter/social.
- Failure cần manual review: tool routing PASS không đồng nghĩa tool execution tốt; các lỗi RapidAPI 403/429 hoặc action `send(confirmed=true)` cần đọc trace/result để hiểu risk thật.
- Improve next: thêm public tunnel/demo URL, chạy thêm live transcript từ UI, và nếu có thời gian thì dùng `dedupe_sources` + `source_triage` trong prompt/tool flow sau khi đã lấy items để cải thiện digest quality.
