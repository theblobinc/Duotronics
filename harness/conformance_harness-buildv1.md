The conformance harness is the **executable test suite that proves an implementation actually follows the rules** laid out in DPFC, the Witness Contract, and the supporting registries. It’s not a single script—it’s a layered, fixture‑driven, repeatable set of checks across transport, canonicalisation, conversion, replay, retention, and policy behaviour.

Below I’ll explain what it is, what it must cover, and then give you a concrete, step‑by‑step plan for building it, based directly on what the source documents require.

---

## 1. What the Conformance Harness Is

From the spec’s own words (DPFC v5.6 §24 & Appendix T, Witness Contract v10.6 §27 & Appendices S/I):

- **“A DPFC implementation should be verified by a conformance harness, not only by prose review.”** (DPFC, App T)
- **“The Witness Contract must be testable through fixtures, golden traces, and negative tests.”** (Witness Contract, App S)
- **“A v10.6 implementation should not pass CI unless all normative fixtures pass; no failed frame enters trusted memory; no absence‑zero collision is accepted; retention metrics have baselines.”** (Witness Contract, App S)

The harness is the **guard** that separates experimental sketches from trustworthy runtimes. It ensures every claim class (C1–C6) is backed by the right evidence: definitions are unambiguous, theorems are verified, invariants hold under transformation, and so on.

In practice, it’s a **test directory** with:

- YAML/JSON fixture packs (the exact same ones embedded in the specs)
- A runner that loads those fixtures, calls your implementation’s equivalents of `evaluate_family_word`, `canonicalize_witness_key_bundle`, `decode_witness8`, etc.
- Assertions that compare output to `expected` values
- Additional fuzz / negative tests that bombard the system with malformed frames, schema mismatches, export‑policy violations
- Golden traces for replay verification
- Retention metric reports that prove baselines are used

The CI pipeline **blocks** a release if any normative fixture fails.

---

## 2. What the Harness Must Test

The specs explicitly list the **required test groups**. You need to cover at least these:

### 2.1 DPFC Core (DPFC §24 & App T)
- Family parser validity
- Bijective bridge (encode/decode round‑trip)
- Successor bridge commutation property
- Addition & multiplication against positive‑index evaluation
- Export boundary affine correction
- Inter‑family conversion with core‑magnitude preservation
- Canonical storage stability (hash invariant under same input)
- Witness degeneracy and canonical representative handling
- Geometry usefulness (if geometry is claimed, does it actually beat a baseline?)
- Retention metrics with baseline comparison

### 2.2 Witness Contract Runtime (Witness Contract §27 & App S)
- Canonicalization: same input → same normal form; explicit materialization; schema version mismatch detection; token‑free absence ≠ numeric zero
- Lookup: hashing uses normal‑form keys; low confidence gates retrieval; bypass overrides injection
- Transport (DBP/WSB2/Witness8):
  - Invalid frame shape → transport_bypass
  - Integrity failure → no semantic decode, no trusted memory write
  - Witness8 field order is enforced
  - All‑inactive row → token_free_absent (not numeric zero)
  - Present numeric zero is distinct when profile supports it
- Bypass modes: the system can enter `degraded`, `family_bypass`, `transport_bypass`, `lookup_bypass`, `full_bypass` under the right conditions
- Replay identity: pinned versions produce identical output; a version change causes replay_mismatch
- Migration: must‑preserve invariants hold; expected losses are declared; a missing migration plan is rejected
- Policy shield: L5 decision matrix is exercised; rollback is possible

### 2.3 Supporting Registries (Extracted Documents)
Each of the extracted baseline specs (Schema Registry, Family Registry, Transport Profiles, Normalizer Profiles, Retention Diagnostics, Policy Shield, Migration Guide) includes its own **conformance checklist** (the last section of each). For example:

- **Family Registry:** evaluation & inverse encoding round‑trip, successor bridge tests, conversion preserves core magnitude, canonical serialisation deterministic
- **Normalizer Profiles:** deterministic normalizer output, explicit failure codes, absence vs. zero distinction, identity‑affecting version pinning
- **Transport Profiles:** transport‑before‑semantics rule, inactive lane ≠ zero, explicit field order for Witness8, replay profile version pinned
- **Retention Diagnostics:** extractor & similarity declared, baseline suite run, metric elasticity prohibited, must‑preserve losses trigger failure action
- **Policy Shield:** L5 forces bypass modes correctly, block promotion when migration missing, emit policy events

Your harness must verify each of those checklists programmatically.

---

## 3. How to Implement the Harness (Step‑by‑Step)

### 3.1 Choose a Test Framework
Pick a unit‑test framework that supports parametric tests and YAML/JSON loading. In the existing specs we use Python with simple `assert` statements (see DPFC App H and Witness Contract Apps I & K). You can extend that.

For a production harness I’d recommend **pytest** because:
- it natively supports fixtures (no relation to Duotronic fixtures—different meaning)
- `pytest.mark.parametrize` can run a single test function over every entry in a fixture file
- it has great plugin support for generating reports, running sub‑selects, and CI integration

### 3.2 Directory Structure (from DPFC App T)
Organise your test tree exactly as the spec suggests. For example:

```
conformance/
├── dpfc_core/
│   ├── fixtures/
│   │   ├── dpfc-core-fixtures.yaml
│   │   └── dpfc-core-fixtures.json
│   ├── test_evaluation.py
│   ├── test_successor.py
│   ├── test_conversion.py
│   ├── test_export.py
│   └── ...
├── witness_contract/
│   ├── fixtures/
│   │   ├── witness-runtime-fixtures.yaml
│   │   └── spectral-edo-fixtures.yaml
│   ├── test_canonicalization.py
│   ├── test_transport.py
│   ├── test_replay.py
│   ├── test_retention.py
│   └── ...
├── transport/
│   ├── test_witness8.py
│   ├── test_dbp.py
│   └── test_wsb2.py
├── registries/
│   ├── test_schema_registry.py
│   ├── test_family_registry.py
│   ├── test_normalizer.py
│   └── ...
├── policy/
│   ├── test_shield.py
│   └── test_migration.py
├── golden_traces/
│   ├── trace_001.yaml
│   └── trace_002.yaml
├── fuzz/
│   └── test_fuzz_malformed.py
└── ci/
    └── acceptance.sh
```

### 3.3 Load Fixture Packs
The specs already provide the exact fixture packs in YAML and JSON (DPFC App H, Witness Contract Apps I & K). Write a small loader that reads a fixture pack, validates its schema, and returns a list of `Fixture` objects.

Example using `pytest` fixture parametrisation:

```python
import yaml, json, pytest

def load_fixtures(pack_path):
    with open(pack_path) as f:
        data = yaml.safe_load(f)   # or json.load
    # validate schema
    assert data["schema_version"] == expected_version
    return data["fixtures"]

# in test file:
@pytest.mark.parametrize("fixture", load_fixtures("conformance/dpfc_core/fixtures/dpfc-core-fixtures.yaml"))
def test_dpfc_fixture(fixture):
    # dispatch to operation
    op = fixture["operation"]
    result = run_operation(op, fixture["given"])
    assert result == fixture["expected"]
    # check claim class, failure action, etc.
```

The `run_operation` function maps operation names to your implementation’s API (e.g., `"evaluate_family_word"` → `my_impl.evaluate_family_word(...)`).

### 3.4 Implement Test Functions by Test Group
For each required test group, write a file that exercises positive, negative, and edge cases, not just the provided fixtures. The fixtures are the **minimum** conformance bar.

Examples:

**test_evaluation.py**
- Evaluate known hex6 words → correct positional value and core magnitude
- Reject empty word (non‑normative)
- Reject unknown digit

**test_successor.py**
- Non‑carry: `h1 h4 → h1 h5`
- Carry: `h6 → h1 h1`, `h1 h6 → h2 h1`
- Apply `evaluate_family_word` to both to verify commutation
- Property‑based test: generate random word, successor, and check that `core_index` increased by 1

**test_witness8.py** (transport)
- All‑inactive row → `token_free_absent`
- Numeric zero row (with support flag) → `present_zero_value`
- Re‑ordered mapping fields must still decode in the fixed order
- Invalid row length → `present_invalid`

**test_canonicalization.py**
- Same semantic input yields identical normal form
- Schema version mismatch → `schema_mismatch`
- Unknown family → `family_bypass_required`
- Normalizer failure → explicit failure code

**test_export.py**
- `core_realized_step_add` via positive index → preservation
- Nonnegative export of `mu_2 ⊕_u mu_3` must return 4, not 3
- Export policy mismatch is detected

**test_replay.py**
- Record a full trace (input hash + all pinned versions) and hash the output normal form
- Change any version component → replay_mismatch
- Golden trace: re‑run and compare hash

**test_retention.py**
- Must have a `RetentionMetricSpec` before evaluation
- A real‑pair conversion must beat the shuffled baseline
- Malformed witnesses score near baseline
- Metric cannot change after results are seen (freeze spec)

**test_policy_shield.py**
- Inject a transport integrity failure → verify runtime enters `transport_bypass` and semantic decode is blocked
- Canonicalisation failure rate spike → `family_bypass`, lookups only via generic path
- Absence‑zero collision attempt → `full_bypass`

### 3.5 Golden Traces
Golden traces are pre‑computed records of an end‑to‑end processing step. You store the input frame, the expected normal‑form key, core magnitude, transport validation status, and any expected losses.

During testing, you replay the input and check that the output matches exactly. This is your strongest replay‑identity guard.

The trace schema can follow the example in Witness Contract Appendix U. Store them in YAML under `conformance/golden_traces/`. A test runner loads each trace, processes it, and asserts equality on all must‑preserve fields.

### 3.6 Fuzz Tests (Negative Testing)
The Witness Contract Appendix S calls for fuzz tests that generate:

- Malformed frames (wrong profile ID, truncated payload, scrambled CRC)
- Reordered mapping fields (to prove field order independence isn’t assumed)
- Invalid digit words
- Unknown family IDs
- Missing Fourier provenance (for spectral witnesses)
- Export‑policy mismatches
- Lossy conversion without expected‑loss declaration

You can implement fuzzers using any random testing library (e.g., `hypothesis` in Python). The important part is that every fuzz‑discovered failure results in a defined rejection state—never a silent acceptance or crash.

### 3.7 CI Integration
The Witness Contract specifies CI acceptance criteria (App S). In practice, you’ll run the harness as part of a merge gate. A typical CI step:

```bash
# run the normative fixtures first; abort on failure
pytest conformance/ -m normatives --strict-markers

# run optional research/metric tests; don't fail on these
pytest conformance/retention/ -m research

# replay all golden traces
pytest golden_traces/

# run a limited fuzz battery on every commit; full fuzz nightly
pytest fuzz/ --fuzz-timeout 300
```

The CI configuration (e.g., `.github/workflows/duotronic-conformance.yml`) should block merging if:
- Any normative test fails
- A failed frame is allowed into trusted memory (this should be impossible if the transport tests are correct)
- Token‑free absence decodes as numeric zero
- Replay test mismatches

### 3.8 Use the Provided Reference Implementations as a Seed
Both DPFC v5.6 Appendix H and the Witness Contract v10.6 Appendices I & K contain **working** Python reference implementations with `run_reference_self_test()` functions. These already test the most critical behaviours:

- Hex6 evaluation, successor, encoding, conversion
- Witness8 decode with absence vs. present‑zero
- DBP frame ingress rejection
- Export correction
- EDO approximation and transposition

You can take those functions, refactor them into a `conformance` directory, and then build the parametrised fixture runner around them. That gives you a passing baseline immediately.

---

## 4. Operationalising the Harness

Once the harness is built, the specs demand that a **release must not promote** a family, adapter, or normalizer unless the harness passes the relevant tests (DPFC App T release gates, Witness Contract App F). So your CI should also run a release‑blocking subset.

Additionally, the **Policy Shield Guide** and **Migration Guide** require that the harness can be re‑run during migration (shadow canonicalisation) to compare old vs. new output. So make sure your harness can accept a `--schema-version` flag or environment variable to switch between registry snapshots.

---

## 5. Summary: What “Implementing the Conformance Harness” Means

| Step | Action |
|------|--------|
| **1. Structure** | Create the directory tree shown above, matching DPFC App T. |
| **2. Fixtures** | Copy the exact YAML/JSON fixture packs from the source documents into `fixtures/` subdirectories. Write a loader that yields test cases. |
| **3. Positive tests** | For each required test group, write `test_*.py` files that parametrically run all given fixtures and also add extra edge‑case assertions. |
| **4. Golden traces** | Store pre‑computed end‑to‑end traces; write a test that replays them and verifies identity. |
| **5. Fuzz tests** | Implement fuzzers for transport, witness rows, and export boundaries. Ensure all fuzz outputs are rejected safely. |
| **6. Retention metrics** | Build tests that run retention measurements and verify that a `RetentionMetricSpec` exists, baselines are used, and elasticity is prohibited. |
| **7. Policy & Bypass** | Test that the L5 shield transitions to the correct mode under fault injection. |
| **8. CI integration** | Add a CI pipeline that runs the normative suite as a merge gate, and do not allow promotion on failure. |
| **9. Migration replay** | Make the harness version‑aware so it can replay under old and new registries for migration validation. |

The end result is a system that **auto‑proves** conformance to the layered Duotronic specs—exactly the kind of engineering rigour the documents demand.