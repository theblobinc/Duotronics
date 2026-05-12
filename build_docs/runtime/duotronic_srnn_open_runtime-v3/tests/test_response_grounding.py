from duotronic_runtime.response_grounding import ground_response, should_repair_duotronic_response


def test_repairs_duotronic_refusal():
    prompt = "Explain Duotronic non-collapse in one precise paragraph."
    response = "I cannot provide information on this topic."
    repaired, meta = ground_response(prompt, response)

    assert meta["applied"] is True
    assert "model output remains evidence rather than truth" in repaired.lower()
    assert "policy approval remains authorization rather than proof" in repaired.lower()


def test_repairs_physics_hallucination():
    prompt = "Explain Duotronic non-collapse."
    response = "This happens when an anode and cathode create voltage collapse in plasma."
    assert should_repair_duotronic_response(prompt, response) is True


def test_does_not_repair_unrelated_response():
    repaired, meta = ground_response("Say hello.", "Hello from Xavi Runtime.")
    assert meta["applied"] is False
    assert repaired == "Hello from Xavi Runtime."
