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


st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")
st.title("Research Agent")

with st.sidebar:
    st.subheader("Run")
    provider_name = st.selectbox("Provider", ["deepseek", "openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.text_input("Version", value="v3")
    model = st.text_input("Model override", value="")
    history_window = st.number_input("History window", min_value=0, max_value=10, value=5)
    max_tool_rounds = st.number_input("Max tool rounds", min_value=1, max_value=8, value=4)
    if st.button("New transcript", use_container_width=True):
        _reset_session()
    st.caption("Transcript is saved after each turn.")

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

metric_cols = st.columns(4)
metric_cols[0].metric("Provider", provider_name)
metric_cols[1].metric("Model", model or getattr(make_provider(provider_name), "default_model", "default"))
metric_cols[2].metric("Tools", str(len(tool_declarations)))
metric_cols[3].metric("Version", artifact_version.artifact_version)

for turn in st.session_state.turns:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        st.write(turn.get("assistant_text") or turn.get("error") or "")
        for round_record in turn.get("rounds", []):
            label = f"Round {round_record.get('round')}: {len(round_record.get('tool_calls', []))} tool call(s)"
            with st.expander(label):
                st.markdown("**Tool calls**")
                st.code(_json(round_record.get("tool_calls", [])), language="json")
                st.markdown("**Tool results**")
                st.code(_json(round_record.get("tool_results", [])), language="json")

prompt = st.chat_input("Ask for web news, tweets, URL summaries, or digests")
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

    with st.spinner("Running agent and tools..."):
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

st.divider()
if st.session_state.transcript:
    path = _transcript_path(st.session_state.transcript)
    st.markdown(f"**Transcript:** `{path}`")
    st.code(_json({
        "artifact_version": st.session_state.transcript.get("artifact_version"),
        "prompt_hash": st.session_state.transcript.get("prompt_hash"),
        "tools_hash": st.session_state.transcript.get("tools_hash"),
        "turn_count": len(st.session_state.transcript.get("turns", [])),
    }), language="json")
else:
    st.markdown("**Transcript:** not started yet")
