from pathlib import Path

from duotronic_runtime.corpus_manager import CorpusManager
from duotronic_runtime.wgrnn import WGRNNRuntime
from duotronic_runtime.api import _messages_for_ollama_chat, _messages_have_images, ChatMessage


def test_wgrnn_load_namespace_pads_legacy_state(tmp_path: Path) -> None:
    runtime = WGRNNRuntime(loop_id="test", node_id="node", state_dim=32, slot_dim=32, num_slots=4, data_dir=tmp_path)
    state_path = tmp_path / "system__default-agent__default-thread.state.json"
    state_path.write_text(
        '{"h":[0.1,0.2],"c":[0.3],"memory_bank":[[0.4]],"slot_meta":[],"step_count":1}'
    )

    runtime.load_namespace("system/default-agent/default-thread")

    assert len(runtime.h) == 32
    assert len(runtime.c) == 32
    assert len(runtime.memory_bank) == 4
    assert all(len(slot) == 32 for slot in runtime.memory_bank)

    result = runtime.step(
        prompt="legacy state should not crash",
        response_text="ok",
        requested_action="observe",
        user_id="test-user",
        agent_id="test-agent",
        thread_id="test-thread",
    )
    assert result["memory_update"]["slot_id"] >= 0


def test_corpus_search_documents_returns_digest_backed_snippet(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text("WG-RNN should use the mounted corpus for LibreChat answers.")
    manager = CorpusManager(tmp_path)

    result = manager.search_documents("why does librechat need wg-rnn corpus", top_k=3)

    assert result["status"] == "ok"
    assert result["results"]
    assert result["results"][0]["path"] == "guide.md"
    assert result["results"][0]["digest"].startswith("sha256:")


def test_messages_for_ollama_chat_preserves_inline_images() -> None:
    msg = ChatMessage(
        role="user",
        content=[
            {"type": "text", "text": "describe this"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,ZmFrZQ=="}},
        ],
    )

    assert _messages_have_images([msg]) is True
    messages = _messages_for_ollama_chat([msg])

    user_messages = [m for m in messages if m["role"] == "user"]
    assert user_messages[-1]["content"] == "describe this"
    assert user_messages[-1]["images"] == ["ZmFrZQ=="]
