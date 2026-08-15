from pathlib import Path

from duotronic_runtime.config import Settings
from duotronic_runtime.corpus_manager import CorpusManager
from duotronic_runtime.runtime_kernel import RuntimeKernel
from duotronic_runtime.wgrnn_kernel_chat import WGRNNKernelChat


def test_wgrnn_kernel_chat_boot_and_prepare(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "README.md").write_text("This corpus is an evidence-language operating corpus.")
    (corpus / "EVIDENCE_LANGUAGE_OPERATING_SYSTEM_PRIMER_v1_0.md").write_text(
        "The execution loop parses operations, emits witnesses, and writes candidate memory."
    )
    (corpus / "executable").mkdir()
    (corpus / "executable" / "kernel").mkdir()
    (corpus / "executable" / "kernel" / "logical_observer_kernel_syscalls.yaml").write_text(
        "syscalls:\n  - corpus.search\n  - memory.write_candidate\n"
    )

    settings = Settings(corpus_dir=corpus, runtime_data_dir=tmp_path / "data")
    runtime = RuntimeKernel(settings)
    kernel_chat = WGRNNKernelChat(runtime)
    search = runtime.corpus_manager.search_documents("operating corpus witnesses", top_k=2)

    prepared = kernel_chat.prepare_turn(
        prompt="How should the WG-RNN use the operating corpus?",
        messages=[],
        corpus_search=search,
    )

    assert prepared["boot"]["status"] in {"safe_mode", "booted"}
    assert prepared["task_frame"]["mode"] == "wg-rnn:chat"
    assert prepared["task_frame"]["operation_kind"] == "ask"
    assert prepared["system_messages"]
    assert prepared["witness_chain"][0]["witness_type"] == "KernelTaskFrameWitness"


def test_wgrnn_kernel_chat_finalize_writes_candidate_memory(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "README.md").write_text("Memory writes are candidate until promoted.")
    settings = Settings(corpus_dir=corpus, runtime_data_dir=tmp_path / "data")
    runtime = RuntimeKernel(settings)
    kernel_chat = WGRNNKernelChat(runtime)
    search = runtime.corpus_manager.search_documents("candidate memory", top_k=2)
    prepared = kernel_chat.prepare_turn(prompt="Remember this as candidate memory", messages=[], corpus_search=search)

    finalized = kernel_chat.finalize_turn(prepared=prepared, response_text="Stored as candidate memory.")

    assert finalized["kernel_turn"]["training_write"] == "candidate_memory"
    assert finalized["kernel_turn"]["promotion"] == "not_promoted"
    assert finalized["wgrnn"]["memory_update"]["trust_status"] in {"candidate", "quarantine"}
    assert finalized["witness_chain"][-1]["witness_type"] == "KernelTurnResultWitness"
