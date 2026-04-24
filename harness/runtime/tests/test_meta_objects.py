from runtime_ref.meta_objects.normalization import canonicalize_meta_bundle, compute_meta_summary, normalize_meta_object


def test_normalize_meta_object_is_deterministic() -> None:
    first = normalize_meta_object(
        {
            "object_id": "  Assertion 1  ",
            "type_name": "Visual Symbol",
            "canonical_name": " Spiral Gate ",
            "category": "visual_symbol",
            "evidence_class": "direct_observation",
            "confidence": 0.81234567,
            "attributes": {"Color": "Blue", "Tags": ["B", "A"]},
            "provenance": {"source": "camera", "frames": [2, 1]},
            "tags": ["Zeta", "alpha", "alpha"],
        }
    )
    second = normalize_meta_object(
        {
            "canonical_name": "spiral gate",
            "type_name": "visual   symbol",
            "category_path": "perceptual/visual_symbol",
            "evidence_class": "direct_observation",
            "confidence": 0.81234567,
            "attributes": {"Tags": ["A", "B"], "Color": "Blue"},
            "provenance": {"frames": [1, 2], "source": "camera"},
            "tags": ["alpha", "zeta"],
            "object_id": "assertion_1",
        }
    )

    assert first == second


def test_canonicalize_meta_bundle_is_order_independent() -> None:
    bundle_a = canonicalize_meta_bundle(
        {
            "bundle_id": " Demo Bundle ",
            "assertions": [
                {
                    "object_id": "b",
                    "type_name": "motif",
                    "canonical_name": "Echo",
                    "category": "motif",
                    "confidence": 0.6,
                },
                {
                    "object_id": "a",
                    "type_name": "scene",
                    "canonical_name": "Night Road",
                    "category": "scene",
                    "confidence": 0.9,
                },
            ],
        }
    )
    bundle_b = canonicalize_meta_bundle(
        {
            "bundle_id": "demo bundle",
            "assertions": list(reversed(bundle_a["assertions"])),
        }
    )

    assert bundle_a["bundle_hash"] == bundle_b["bundle_hash"]


def test_compute_meta_summary_counts_categories() -> None:
    summary = compute_meta_summary(
        {
            "bundle_id": "summary",
            "assertions": [
                {"object_id": "1", "type_name": "scene", "canonical_name": "Night", "category": "scene", "confidence": 0.9},
                {"object_id": "2", "type_name": "motif", "canonical_name": "Echo", "category": "motif", "confidence": 0.5},
                {"object_id": "3", "type_name": "motif", "canonical_name": "Return", "category": "motif", "confidence": 0.7},
            ],
        }
    )

    assert summary["assertion_count"] == 3
    assert summary["counts_by_category"] == {"perceptual/scene": 1, "semantic/motif": 2}