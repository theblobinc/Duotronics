#!/usr/bin/env python3
"""Draft 5.2 corpus-local validation helper.
This script performs portable checks that do not require network access.
Install jsonschema for full instance validation; without it, parse and inventory checks still run.
"""
from __future__ import annotations
import json, hashlib, sys, sqlite3, re
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

CLAIM_STATUS_MAP_LEAN = {
    'unknown':'unknown','absent':'absent','invalid':'invalid','draft':'draft','observed':'observed','computed':'computed',
    'proposed':'proposed','asserted':'asserted','deferred':'deferred','vetoed':'vetoed','conjecture':'conjecture','theorem':'theorem',
    'replay_verified':'replayVerified','proof_verified':'proofVerified','policy_approved':'policyApproved','released':'released'
}
PRIMITIVE_MAP_LEAN = {
    'zero':'zero','absence':'absence','unknown':'unknown','invalid':'invalid','empty':'empty','null':'nullValue',
    'computational_evidence':'computationalEvidence','theorem':'theorem','conjectural':'conjectural','self_trained':'selfTrained',
    'authoritative':'authoritative','audit_only':'auditOnly','active':'active','observation':'observation','proof':'proof',
    'explanation':'explanation','fact':'fact','policy_approval':'policyApproval','human_attestation':'humanAttestation',
    'synthetic_witness':'syntheticWitness','activation_witness':'activationWitness'
}

def rel(p): return p.relative_to(ROOT).as_posix()
def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load_json(path): return json.loads((ROOT/path).read_text())

def validate_instance(schema_path, instance, errors, label, expect_valid=True):
    if not jsonschema:
        return
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    validation_errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    if expect_valid and validation_errors:
        errors.append(f'{label}: {validation_errors[0].message}')
    if not expect_valid and not validation_errors:
        errors.append(f'{label}: invalid fixture unexpectedly passed')

def fixture_schema_payload(fp):
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
        raise ValueError(f'fixture lacks schema_ref/payload and has no legacy mapping: {fp}')
    return legacy[name], data

def extract_json_enum(schema_path, prop):
    data = load_json(schema_path)
    return data['properties'][prop]['enum']

def check_formal_parity(errors):
    statuses = extract_json_enum('schemas/evidence_claim.schema.json', 'claim_status')
    lean = (ROOT/'formal/lean4/DuotronicEvidenceSyntax.lean').read_text()
    tla = (ROOT/'formal/tlaplus/EvidenceClaimGraph.tla').read_text()
    for s in statuses:
        if CLAIM_STATUS_MAP_LEAN[s] not in lean:
            errors.append(f'formal_status_parity: Lean missing {s}')
        if f'"{s}"' not in tla:
            errors.append(f'formal_status_parity: TLA missing {s}')
    primitives = extract_json_enum('schemas/non_collapse_state.schema.json', 'primitive_category')
    lean_meta = (ROOT/'formal/lean4/DuotronicCoreMetaphysics.lean').read_text()
    tla_nc = (ROOT/'formal/tlaplus/NonCollapseAxioms.tla').read_text()
    for p in primitives:
        if PRIMITIVE_MAP_LEAN[p] not in lean_meta:
            errors.append(f'primitive_state_parity: Lean missing {p}')
        if f'"{p}"' not in tla_nc:
            errors.append(f'primitive_state_parity: TLA missing {p}')
    if 'PairClass' not in tla_nc or 'ProofWitnessRequired' not in tla_nc or 'AuthorityWitnessRequired' not in tla_nc:
        errors.append('primitive_state_parity: TLA non-collapse witness classes missing')

def check_kernel_syscalls(errors):
    if not yaml:
        return
    p = ROOT/'executable/kernel/logical_observer_kernel_syscalls.yaml'
    if not p.exists():
        errors.append('kernel_syscall_coverage: missing executable/kernel/logical_observer_kernel_syscalls.yaml')
        return
    data = yaml.safe_load(p.read_text())
    if not data.get('deterministic'):
        errors.append('kernel_syscall_coverage: syscall grammar must be deterministic')
    if len(data.get('invariants', [])) != 10:
        errors.append('kernel_syscall_coverage: expected 10 kernel invariants')
    required = {'observe','compose','infer','verify','replay','delegate','promote','compute','adjudicate','rollback','export'}
    got = {s.get('name') for s in data.get('syscalls', [])}
    missing = sorted(required - got)
    if missing:
        errors.append(f'kernel_syscall_coverage: missing syscalls {missing}')

def check_normative_coverage(errors):
    p = ROOT/'refs/normative_rule_coverage_matrix_v1_6_draft_5_2.json'
    if not p.exists():
        errors.append('normative_rule_coverage_check: missing coverage matrix')
        return
    data = json.loads(p.read_text())
    rules = data.get('rules', [])
    ids = {r.get('rule_id') for r in rules}
    expected = {f'K{i}' for i in range(1,11)}
    if ids != expected:
        errors.append(f'normative_rule_coverage_check: expected K1-K10 got {sorted(ids)}')
    for r in rules:
        for key in ['contract']:
            if not (ROOT/r[key]).exists():
                errors.append(f'normative_rule_coverage_check: missing {r[key]}')
        for sp in r.get('schemas', []):
            if not (ROOT/sp).exists():
                errors.append(f'normative_rule_coverage_check: missing {sp}')
        for fp in r.get('fixtures', []):
            if not (ROOT/fp).exists():
                errors.append(f'normative_rule_coverage_check: missing {fp}')


def check_tla_toolchain(errors):
    manifest_path = ROOT/'refs/formal_toolchain/tla_toolchain_manifest_v1_0.json'
    runner_path = ROOT/'executable/formal/run_tla_model_check.py'
    if not manifest_path.exists():
        errors.append('tla_toolchain_check: missing refs/formal_toolchain/tla_toolchain_manifest_v1_0.json')
        return
    if not runner_path.exists():
        errors.append('tla_toolchain_check: missing executable/formal/run_tla_model_check.py')
        return
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:
        errors.append(f'tla_toolchain_check: manifest parse failed: {e}')
        return
    if manifest.get('integration_scope') != 'tla_plus_only':
        errors.append('tla_toolchain_check: integration_scope must be tla_plus_only')
    if manifest.get('lean_toolchain_added') is not False:
        errors.append('tla_toolchain_check: Lean toolchain must not be added in TLA-only integration')
    for entry in manifest.get('tla_modules', []):
        for key in ['spec', 'config']:
            if not (ROOT/entry[key]).exists():
                errors.append(f'tla_toolchain_check: missing {entry[key]}')
        cfg = ROOT/entry.get('config', '')
        spec = ROOT/entry.get('spec', '')
        if cfg.exists():
            cfg_text = cfg.read_text()
            if 'SPECIFICATION Spec' not in cfg_text:
                errors.append(f'tla_toolchain_check: {entry.get("config")} missing SPECIFICATION Spec')
            if 'INVARIANTS' not in cfg_text:
                errors.append(f'tla_toolchain_check: {entry.get("config")} missing INVARIANTS')
        if spec.exists():
            spec_text = spec.read_text()
            if f'MODULE {entry.get("module")}' not in spec_text:
                errors.append(f'tla_toolchain_check: {entry.get("spec")} module header mismatch')
            if 'Spec ==' not in spec_text:
                errors.append(f'tla_toolchain_check: {entry.get("spec")} missing Spec operator')
    import subprocess
    proc = subprocess.run([sys.executable, str(runner_path), '--mode', 'advisory', '--json'], cwd=ROOT, text=True, capture_output=True, timeout=30)
    if proc.returncode != 0:
        errors.append('tla_toolchain_check: advisory runner failed: ' + (proc.stdout + proc.stderr)[-1000:])


def main():
    errors=[]
    for p in ROOT.glob('schemas/*.schema.json'):
        try:
            data=json.loads(p.read_text())
            if jsonschema:
                jsonschema.Draft202012Validator.check_schema(data)
        except Exception as e:
            errors.append(f'schema {rel(p)}: {e}')
    if yaml:
        for p in list(ROOT.glob('executable/openapi/*.yaml')) + list(ROOT.glob('executable/kernel/*.yaml')):
            try: yaml.safe_load(p.read_text())
            except Exception as e: errors.append(f'yaml {rel(p)}: {e}')
    try:
        sql=(ROOT/'executable/sql/draft5_2_schema_additions.sql').read_text()
        con=sqlite3.connect(':memory:')
        con.executescript(sql)
        # Minimal guard checks for kernel additions.
        try:
            con.execute("INSERT INTO srnn_resource_budget_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                'budget:bad','resource_budget_witness/v1','task:bad',1,0,1,1,1,0,0,0,1,'policy:bad','2026-05-11T00:00:00Z'))
            errors.append('sql guard: resource budget allowed network unexpectedly inserted')
        except sqlite3.IntegrityError:
            pass
        try:
            con.execute("INSERT INTO srnn_kernel_transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                'tx:bad','kernel_transaction/v1','task:bad','evidence','committed','[]','[]','[]',1,'policy:bad',None,'2026-05-11T00:00:00Z',None))
            errors.append('sql guard: committed transaction without witnesses unexpectedly inserted')
        except (sqlite3.IntegrityError, sqlite3.OperationalError):
            pass
        con.close()
    except Exception as e:
        errors.append(f'sql: {e}')
    inv=json.loads((ROOT/'PACKAGE_INVENTORY_v1_6_draft_5_2.json').read_text())
    actual_files=[p for p in ROOT.rglob('*') if p.is_file()]
    if inv.get('file_count') != len(actual_files):
        errors.append(f'inventory file_count {inv.get("file_count")} != actual {len(actual_files)}')
    excluded=set(inv.get('canonical_hash_scope',{}).get('excluded_paths', []))
    actual_hash_count=sum(1 for p in actual_files if rel(p) not in excluded)
    if inv.get('hash_closure_file_count') != actual_hash_count:
        errors.append(f'inventory hash_closure_file_count {inv.get("hash_closure_file_count")} != actual {actual_hash_count}')
    inv_paths = {rec['path'] for rec in inv['files']}
    for p in actual_files:
        if rel(p) not in inv_paths:
            errors.append(f'missing inventory record {rel(p)}')
    for rec in inv['files']:
        p=ROOT/rec['path']
        if not p.exists():
            errors.append(f'missing inventory path {rec["path"]}')
            continue
        if not rec.get('excluded_from_hash_closure') and p.stat().st_size != rec.get('size_bytes'):
            errors.append(f'size mismatch {rec["path"]}')
        if not rec.get('excluded_from_hash_closure'):
            got=sha256(p)
            if got != rec.get('sha256'):
                errors.append(f'hash mismatch {rec["path"]}')
    if jsonschema:
        try:
            vectors=load_json('executable/tests/draft5_2_conformance_vectors.json')
            for fp in vectors.get('valid_fixtures', []):
                try:
                    sp, payload = fixture_schema_payload(fp)
                    validate_instance(sp, payload, errors, f'fixture {fp}', expect_valid=True)
                except Exception as e:
                    errors.append(f'fixture {fp}: {e}')
            for fp in vectors.get('invalid_fixtures', []):
                try:
                    sp, payload = fixture_schema_payload(fp)
                    validate_instance(sp, payload, errors, f'invalid fixture {fp}', expect_valid=False)
                except Exception as e:
                    errors.append(f'invalid fixture {fp}: {e}')
        except Exception as e:
            errors.append(f'conformance vectors invalid: {e}')
    check_formal_parity(errors)
    check_kernel_syscalls(errors)
    check_normative_coverage(errors)
    if errors:
        print('\n'.join(errors))
        return 1
    print('Draft 5.2 corpus validation checks passed.')
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
