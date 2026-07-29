from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    ARTIFACTS_DIR,
    ROOT,
    now_iso,
    run_model_tool_loop,
    safe_slug,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


load_lab_env(ROOT)

TRANSCRIPTS_DIR = ROOT / "transcripts"


CSS = """
<style>
:root {
  --surface: oklch(17% 0.012 242);
  --surface-raised: oklch(21% 0.016 242);
  --surface-muted: oklch(14% 0.012 242);
  --surface-soft: oklch(25% 0.018 242);
  --line: oklch(32% 0.02 242);
  --line-strong: oklch(44% 0.025 242);
  --text: oklch(91% 0.012 242);
  --text-muted: oklch(68% 0.018 242);
  --accent: oklch(72% 0.105 190);
  --accent-strong: oklch(80% 0.125 190);
  --accent-soft: oklch(28% 0.045 190);
  --success: oklch(74% 0.12 154);
  --warning: oklch(80% 0.13 78);
  --danger: oklch(72% 0.14 28);
}

.stApp {
  background: var(--surface);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}

section[data-testid="stSidebar"] {
  background: var(--surface-muted);
  border-right: 1px solid var(--line);
}

section[data-testid="stSidebar"] * {
  font-size: 0.92rem;
  color: var(--text);
}

section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stCaptionContainer,
section[data-testid="stSidebar"] p {
  color: var(--text-muted) !important;
}

.block-container {
  max-width: 1180px;
  padding-top: 1.1rem;
  padding-bottom: 2.25rem;
}

h1, h2, h3 {
  color: var(--text);
  letter-spacing: 0;
}

h1 {
  font-size: 1.65rem;
  line-height: 1.2;
  font-weight: 720;
  margin: 0;
}

.agent-topbar {
  border: 1px solid var(--line);
  background: var(--surface-raised);
  border-radius: 8px;
  padding: 16px 18px 15px;
  margin-bottom: 12px;
}

.agent-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.agent-subtitle {
  max-width: 68ch;
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 0.95rem;
  line-height: 1.5;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--line);
  margin: 12px 0 18px;
}

.status-cell {
  min-width: 0;
  background: var(--surface-raised);
  padding: 11px 13px;
}

.status-label {
  color: var(--text-muted);
  font-size: 0.72rem;
  font-weight: 650;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.status-value {
  color: var(--text);
  font-size: 0.9rem;
  font-weight: 650;
  line-height: 1.35;
  margin-top: 3px;
  overflow-wrap: anywhere;
}

.trace-empty {
  border: 1px dashed var(--line);
  border-radius: 8px;
  background: var(--surface-muted);
  padding: 18px;
  color: var(--text-muted);
  margin-top: 8px;
}

.turn-meta {
  color: var(--text-muted);
  font-size: 0.78rem;
  margin: 4px 0 8px;
}

.tool-pill {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--accent-soft);
  color: var(--accent-strong);
  font-size: 0.78rem;
  font-weight: 650;
  margin: 0 5px 5px 0;
}

.transcript-path {
  border: 1px solid var(--line);
  background: var(--surface-raised);
  border-radius: 8px;
  padding: 12px 14px;
  color: var(--text-muted);
  overflow-wrap: anywhere;
}

div[data-testid="stChatMessage"] {
  border-radius: 8px;
  background: var(--surface-raised);
  border: 1px solid var(--line);
}

div[data-testid="stExpander"] {
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface-raised);
}

div[data-testid="stCodeBlock"] {
  border: 1px solid var(--line);
  border-radius: 8px;
}

.stButton > button,
.stDownloadButton > button {
  min-height: 42px;
  border-radius: 7px;
  border: 1px solid var(--line);
  background: var(--surface-soft);
  color: var(--text);
  font-weight: 650;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--surface-raised);
}

.stButton > button:focus-visible,
.stDownloadButton > button:focus-visible,
input:focus-visible,
textarea:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-baseweb="select"] > div {
  background: var(--surface-raised);
  border-color: var(--line);
  color: var(--text);
  border-radius: 7px;
}

button[kind="secondary"] {
  background: var(--surface-soft);
}

.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  border-bottom: 1px solid var(--line);
}

.stTabs [data-baseweb="tab"] {
  color: var(--text-muted);
  border-radius: 7px 7px 0 0;
  padding: 8px 12px;
}

.stTabs [aria-selected="true"] {
  color: var(--accent-strong) !important;
  background: var(--surface-raised);
}

.stTabs [data-baseweb="tab-highlight"] {
  background-color: var(--accent) !important;
}

div[data-testid="stChatInput"] {
  background: var(--surface-muted);
  border-top: 1px solid var(--line);
}

div[data-testid="stChatInput"] textarea {
  background: var(--surface-raised);
  color: var(--text);
  border: 1px solid var(--line);
  border-radius: 8px;
}

div[data-testid="stToolbar"],
header[data-testid="stHeader"] {
  background: var(--surface-muted);
}

@media (max-width: 760px) {
  .block-container {
    padding: 1rem 0.75rem 1.75rem;
  }

  .agent-title-row {
    display: block;
  }

  .status-strip {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
"""


def _json(value: Any, max_chars: int = 12000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        return text[:max_chars] + "\n...<truncated>"
    return text


def _new_transcript(version: str, provider_name: str, model: str | None, history_window: int, max_tool_rounds: int) -> dict[str, Any]:
    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    provider = make_provider(provider_name)
    selected_model = model or getattr(provider, "default_model", None)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), timestamp])
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)
    return {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": selected_model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": history_window,
        "max_tool_rounds": max_tool_rounds,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def _transcript_path(transcript: dict[str, Any]) -> Path:
    return TRANSCRIPTS_DIR / f"{transcript['transcript_id']}.transcript.json"


def _reset_session() -> None:
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.transcript = None


def _render_turn_trace(turn: dict[str, Any], *, expanded: bool = False) -> None:
    rounds = turn.get("rounds", [])
    if not rounds:
        st.caption("No structured trace was recorded for this turn.")
        return

    for round_record in rounds:
        call_count = len(round_record.get("tool_calls", []))
        result_count = len(round_record.get("tool_results", []))
        label = f"Round {round_record.get('round')} | calls {call_count} | results {result_count}"
        with st.expander(label, expanded=expanded and bool(call_count)):
            if round_record.get("assistant_text"):
                st.markdown("**Assistant routing note**")
                st.write(round_record.get("assistant_text"))

            calls_col, results_col = st.columns(2)
            with calls_col:
                st.markdown("**Tool calls**")
                st.code(_json(round_record.get("tool_calls", [])), language="json")
            with results_col:
                st.markdown("**Tool results**")
                st.code(_json(round_record.get("tool_results", [])), language="json")


st.set_page_config(page_title="Research Agent", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.subheader("Run Settings")
    provider_name = st.selectbox("Provider", ["deepseek", "openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.text_input("Version", value="v3")
    model = st.text_input("Model override", value="")
    history_window = st.number_input("History window", min_value=0, max_value=10, value=5)
    max_tool_rounds = st.number_input("Max tool rounds", min_value=1, max_value=8, value=4)
    if st.button("Start new transcript", use_container_width=True):
        _reset_session()

if "history" not in st.session_state:
    st.session_state.history = []
if "turns" not in st.session_state:
    st.session_state.turns = []
if "transcript" not in st.session_state:
    st.session_state.transcript = None

system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"
system_prompt = system_prompt_path.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)
artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

selected_model = model or getattr(make_provider(provider_name), "default_model", "default")

st.markdown(
    f"""
    <div class="agent-topbar">
      <div class="agent-title-row">
        <div>
          <h1>Research Agent Console</h1>
          <div class="agent-subtitle">Live agent surface for requests, final responses, tool traces, run identity, and saved transcripts.</div>
        </div>
      </div>
    </div>
    <div class="status-strip">
      <div class="status-cell"><div class="status-label">Provider</div><div class="status-value">{provider_name}</div></div>
      <div class="status-cell"><div class="status-label">Model</div><div class="status-value">{selected_model}</div></div>
      <div class="status-cell"><div class="status-label">Tools</div><div class="status-value">{len(tool_declarations)}</div></div>
      <div class="status-cell"><div class="status-label">Artifact</div><div class="status-value">{artifact_version.artifact_version}</div></div>
    </div>
    """,
    unsafe_allow_html=True,
)

chat_tab, trace_tab, transcript_tab = st.tabs(["Chat", "Trace", "Transcript"])

with chat_tab:
    if not st.session_state.turns:
        st.markdown('<div class="trace-empty">No turns yet. Run a scenario to create trace evidence.</div>', unsafe_allow_html=True)

    for turn in st.session_state.turns:
        with st.chat_message("user"):
            st.write(turn["user"])
        with st.chat_message("assistant"):
            st.markdown(f'<div class="turn-meta">Status: {turn.get("status", "unknown")}</div>', unsafe_allow_html=True)
            st.write(turn.get("assistant_text") or turn.get("error") or "")
            tool_names = [
                call.get("name", "")
                for round_record in turn.get("rounds", [])
                for call in round_record.get("tool_calls", [])
            ]
            if tool_names:
                pills = "".join(f'<span class="tool-pill">{name}</span>' for name in tool_names)
                st.markdown(pills, unsafe_allow_html=True)
            with st.expander("Xem cách suy luận của bot (decision trace)", expanded=False):
                st.caption("Hiển thị evidence quan sát được: tool nào được chọn, arguments, result/error và status. Không hiển thị private chain-of-thought ẩn của model.")
                _render_turn_trace(turn)

with trace_tab:
    if not st.session_state.turns:
        st.markdown('<div class="trace-empty">No trace recorded.</div>', unsafe_allow_html=True)

    for turn in st.session_state.turns:
        st.markdown(f"#### Turn {turn['turn_index']}")
        st.caption(turn["user"])
        _render_turn_trace(turn, expanded=True)

with transcript_tab:
    if st.session_state.transcript:
        path = _transcript_path(st.session_state.transcript)
        st.markdown(f'<div class="transcript-path">{path}</div>', unsafe_allow_html=True)
        st.code(_json({
            "artifact_version": st.session_state.transcript.get("artifact_version"),
            "prompt_hash": st.session_state.transcript.get("prompt_hash"),
            "tools_hash": st.session_state.transcript.get("tools_hash"),
            "turn_count": len(st.session_state.transcript.get("turns", [])),
        }), language="json")
    else:
        st.markdown('<div class="trace-empty">Transcript will appear after the first turn.</div>', unsafe_allow_html=True)

prompt = st.chat_input("Enter research request")
if prompt:
    if st.session_state.transcript is None:
        st.session_state.transcript = _new_transcript(
            version=version,
            provider_name=provider_name,
            model=model or None,
            history_window=int(history_window),
            max_tool_rounds=int(max_tool_rounds),
        )

    turn_index = len(st.session_state.turns) + 1
    turn_record: dict[str, Any] = {
        "turn_index": turn_index,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, int(history_window)),
        {"role": "user", "content": prompt},
    ]

    with st.spinner("Running agent and tools"):
        try:
            provider = make_provider(provider_name)
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=model or None,
                max_tool_rounds=int(max_tool_rounds),
            )
            turn_record.update(result)
            st.session_state.history.append({"role": "user", "content": prompt})
            st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:
            turn_record.update({
                "status": "provider_error",
                "error": f"{type(exc).__name__}: {str(exc)}",
                "assistant_text": f"Provider error: {type(exc).__name__}: {str(exc)}",
            })

    turn_record["ended_at"] = now_iso()
    st.session_state.turns.append(turn_record)
    st.session_state.transcript["turns"].append(turn_record)
    path = _transcript_path(st.session_state.transcript)
    write_transcript(path, st.session_state.transcript)
    st.rerun()
