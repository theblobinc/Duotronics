#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sqlite3, subprocess, sys, shutil, re
from pathlib import Path
try:
    import yaml
except Exception:
    yaml = None
try:
    import jsonschema
except Exception:
    jsonschema = None

ROOT = Path(__file__).resolve().parents[2]

def rel(p: Path) -> str: return p.relative_to(ROOT).as_posix()
def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_json(path: str): return json.loads((ROOT / path).read_text())
def fixture_schema_payload(fp: str):
    data = load_json(fp)
    if isinstance(data, dict) and 'schema_ref' in data and 'payload' in data:
        return data['schema_ref'], data['payload']
    legacy = {
      'valid_evidence_claim.fixture.json':'schemas/evidence_claim.schema.json',
      'valid_non_collapse_state.fixture.json':'schemas/non_collapse_state.schema.json',
      'valid_non_collapse_transition.fixture.json':'schemas/non_collapse_transition.schema.json',
      'valid_verification_grammar.fixture.json':'schemas/verification_grammar.schema.json',
      'valid_replay_assumption_manifest.fixture.json':'schemas/replay_assumption_manifest.schema.json',
      'valid_pragmatic_context.fixture.json':'schemas/pragmatic_context.schema.json',
    }
    name = Path(fp).name
    if name not in legacy:
        raise ValueError(f'fixture lacks schema_ref/payload and no legacy mapping: {fp}')
    return legacy[name], data

def validate_instance(schema_path, payload, errors, label, expect_valid=True):
    if not jsonschema:
        return
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if expect_valid and errs:
        errors.append(f'{label}: {errs[0].message}')
    if not expect_valid and not errs:
        errors.append(f'{label}: invalid fixture unexpectedly passed')

def enum(schema, prop):
    return load_json(schema)['properties'][prop]['enum']

def check_formal_parity(errors):
    lean = (ROOT/'Duotronic/EvidenceSyntax.lean').read_text()
    tla = (ROOT/'formal/tlaplus/EvidenceClaimGraph.tla').read_text()
    m = {'replay_verified':'replayVerified','proof_verified':'proofVerified','policy_approved':'policyApproved'}
    for s in enum('schemas/evidence_claim.schema.json','claim_status'):
        token = m.get(s, s)
        if token not in lean:
            errors.append(f'lean status parity missing {s}')
        if f'"{s}"' not in tla:
            errors.append(f'tla status parity missing {s}')
    meta = (ROOT/'Duotronic/CoreMetaphysics.lean').read_text()
    tla_nc = (ROOT/'formal/tlaplus/NonCollapseAxioms.tla').read_text()
    pm = {'null':'nullValue','computational_evidence':'computationalEvidence','self_trained':'selfTrained','audit_only':'auditOnly','policy_approval':'policyApproval','human_attestation':'humanAttestation','synthetic_witness':'syntheticWitness','activation_witness':'activationWitness'}
    for p in enum('schemas/non_collapse_state.schema.json','primitive_category'):
        if pm.get(p,p) not in meta:
            errors.append(f'lean primitive parity missing {p}')
        if f'"{p}"' not in tla_nc:
            errors.append(f'tla primitive parity missing {p}')

def check_kernel_syscalls(errors):
    if not yaml: return
    data = yaml.safe_load((ROOT/'executable/kernel/logical_observer_kernel_syscalls.yaml').read_text())
    got = {s.get('name') for s in data.get('syscalls', [])}
    required = {'observe','compose','infer','verify','replay','delegate','promote','compute','adjudicate','rollback','export','check_proof'}
    missing = sorted(required - got)
    if missing:
        errors.append(f'kernel syscalls missing {missing}')
    cp = next((s for s in data.get('syscalls', []) if s.get('name') == 'check_proof'), None)
    if not cp or set(cp.get('required_witness', [])) != {'LeanCompilerWitness','ProofWitness'}:
        errors.append('check_proof syscall must require LeanCompilerWitness and ProofWitness')
    if len(data.get('invariants', [])) != 10:
        errors.append('kernel invariants count changed from K1-K10')

def check_lean_static_and_runner(errors):
    required = ['lean-toolchain','lakefile.lean','Duotronic.lean','Duotronic/All.lean','Duotronic/ProofAuthority.lean','Duotronic/Kernel.lean','refs/formal_toolchain/lean_toolchain_manifest_v1_0.json']
    for r in required:
        if not (ROOT/r).exists():
            errors.append(f'missing Lean artifact {r}')
    proc = subprocess.run([sys.executable, 'executable/formal/run_lean_build.py', '--mode', 'advisory', '--json'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        errors.append('lean advisory runner failed: ' + (proc.stdout + proc.stderr)[-1000:])
        return
    try:
        data = json.loads(proc.stdout)
    except Exception as e:
        errors.append(f'lean runner did not emit JSON: {e}')
        return
    if data.get('forbidden_markers'):
        errors.append('Lean executable code contains forbidden markers: ' + repr(data.get('forbidden_markers')))
    if data.get('unapproved_axiom_files'):
        errors.append('Lean executable code contains unapproved axioms: ' + repr(data.get('unapproved_axiom_files')))
    if data.get('status') not in {'passed','advisory_pass_lake_unavailable'}:
        errors.append('unexpected Lean advisory status: ' + str(data.get('status')))

def check_sql(errors):
    try:
        con = sqlite3.connect(':memory:')
        con.executescript((ROOT/'executable/sql/draft5_2_schema_additions.sql').read_text())
        try:
            con.execute("INSERT INTO srnn_lean_compiler_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('lean:bad','lean_compiler_witness/v1','leanprover/lean4:v4.29.1','a'*64,'b'*64,'["lake","build"]','passed',1,0,0,'["Duotronic"]','[]',None,None,'2026-05-11T00:00:00Z'))
            errors.append('sql guard: Lean passed with contains_sorry inserted')
        except sqlite3.IntegrityError:
            pass
        try:
            con.execute("INSERT INTO srnn_theorem_promotion_gates VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ('gate:bad','theorem_promotion_gate/v1','claim:1','tx:1','proof:1','lean:1','nc:1','policy:1',1,0,None,'2026-05-11T00:00:00Z'))
            errors.append('sql guard: theorem gate allowed with hash mismatch inserted')
        except sqlite3.IntegrityError:
            pass
        con.close()
    except Exception as e:
        errors.append(f'sql parse/apply failed: {e}')

def check_inventory(errors):
    inv = load_json('PACKAGE_INVENTORY_v1_6_draft_5_2_1.json')
    files = [p for p in ROOT.rglob('*') if p.is_file()]
    if inv.get('file_count') != len(files):
        errors.append(f'inventory file_count {inv.get("file_count")} != actual {len(files)}')
    inv_paths = {r['path'] for r in inv['files']}
    for p in files:
        if rel(p) not in inv_paths:
            errors.append(f'missing inventory record {rel(p)}')
    for rec in inv['files']:
        p = ROOT / rec['path']
        if not p.exists():
            errors.append(f'missing inventory path {rec["path"]}')
            continue
        if not rec.get('excluded_from_hash_closure'):
            if p.stat().st_size != rec.get('size_bytes'):
                errors.append(f'size mismatch {rec["path"]}')
            if sha256(p) != rec.get('sha256'):
                errors.append(f'hash mismatch {rec["path"]}')

def check_fixtures(errors):
    if not jsonschema: return
    vectors = load_json('executable/tests/draft5_2_conformance_vectors.json')
    for fp in vectors.get('valid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, errors, f'fixture {fp}', True)
    for fp in vectors.get('invalid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, errors, f'invalid fixture {fp}', False)

def main():
    errors=[]
    for p in ROOT.glob('schemas/*.schema.json'):
        try:
            data=json.loads(p.read_text())
            if jsonschema: jsonschema.Draft202012Validator.check_schema(data)
        except Exception as e:
            errors.append(f'schema {rel(p)}: {e}')
    if yaml:
        for p in list(ROOT.glob('executable/openapi/*.yaml')) + list(ROOT.glob('executable/kernel/*.yaml')):
            try: yaml.safe_load(p.read_text())
            except Exception as e: errors.append(f'yaml {rel(p)}: {e}')
    check_fixtures(errors)
    check_sql(errors)
    check_formal_parity(errors)
    check_kernel_syscalls(errors)
    check_lean_static_and_runner(errors)
    check_inventory(errors)
    if errors:
        print('\n'.join(errors))
        return 1
    print('Draft 5.2.1 corpus validation checks passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
