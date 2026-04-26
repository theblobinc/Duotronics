from duotronic_wgrnn.runner import run_sample_loop


def test_sample_loop_runs_and_emits_four_records() -> None:
    records = run_sample_loop(return_records=True)
    assert len(records) == 4
    assert [record.witness_feature_vector_id for record in records] == [
        "wfv-001-valid-candidate-write",
        "wfv-002-quarantine",
        "wfv-003-transport-failed",
        "wfv-004-invalidation-block",
    ]


def test_sample_loop_expected_update_kinds() -> None:
    records = {record.witness_feature_vector_id: record for record in run_sample_loop(return_records=True)}
    assert records["wfv-001-valid-candidate-write"].update_kind == "candidate_write"
    assert records["wfv-002-quarantine"].update_kind == "quarantine_write"
    assert records["wfv-003-transport-failed"].update_kind == "no_op"
    assert records["wfv-004-invalidation-block"].update_kind == "no_op"
    assert records["wfv-003-transport-failed"].affected_slot_ids == []
    assert records["wfv-004-invalidation-block"].affected_slot_ids == []
