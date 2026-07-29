# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team:
- Members:
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

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên | tools/dedupe_sources/TOOL.md, tools/dedupe_sources/tool.py | Smoke test pass: input_count=3, output_count=2, removed_count=1 | Local only, no secret, no side effect |
| Additional local tool | tools/source_triage/TOOL.md, tools/source_triage/tool.py | Smoke test pass: ranks items and returns warnings | Triage score is heuristic, not factual verification |
| Provider/API smoke tests | terminal evidence | DeepSeek preflight, lookup, fetch, timeline, social_search pass | API quota/rate limits still need manual monitoring |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?
