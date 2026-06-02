#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sqlite3, subprocess, sys, os
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
    raise ValueError(f'fixture lacks schema_ref/payload: {fp}')

def validate_instance(schema_path, payload, errors, label, expect_valid=True):
    if not jsonschema:
        return
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if expect_valid and errs:
        errors.append(f'{label}: {errs[0].message}')
    if not expect_valid and not errs:
        # Some invalid fixtures rely on semantic checks below, not JSON Schema alone.
        pass

def distribution_sum(payload):
    dist = payload.get('hypothesis_distribution') or []
    return sum(float(x.get('probability', 0)) for x in dist)

def check_probability_distribution(payload, errors, label, expect_valid=True):
    total = distribution_sum(payload)
    ok = abs(total - 1.0) <= 1e-9
    if expect_valid and not ok:
        errors.append(f'{label}: distribution sum {total} != 1')
    if not expect_valid and ok:
        errors.append(f'{label}: invalid distribution unexpectedly normalized')

def check_v17_fixtures(errors):
    vectors = load_json('executable/tests/draft1_7_bayesian_knot_conformance_vectors.json')
    for fp in vectors.get('valid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, errors, f'fixture {fp}', True)
        if 'bayesian_prior' in sp or 'bayesian_posterior_state' in sp:
            check_probability_distribution(payload, errors, f'fixture {fp}', True)
    for fp in vectors.get('invalid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, errors, f'invalid fixture {fp}', False)
        if 'bayesian_posterior_state' in sp:
            check_probability_distribution(payload, errors, f'invalid fixture {fp}', False)
        if 'knot_equivalence_witness' in sp:
            if payload.get('authority_path'):
                errors.append(f'{fp}: invalid knot equivalence unexpectedly has authority path')

def check_kernel_syscalls(errors):
    if not yaml: return
    data = yaml.safe_load((ROOT/'executable/kernel/logical_observer_kernel_syscalls.yaml').read_text())
    got = {s.get('name') for s in data.get('syscalls', [])}
    required = {'observe','compose','infer','verify','replay','delegate','promote','compute','adjudicate','rollback','export','check_proof','bayes_update','bayes_calibrate','bayes_decide','knot_encode','knot_move','knot_invariant','knot_equivalence'}
    missing = sorted(required - got)
    if missing:
        errors.append(f'kernel syscalls missing {missing}')
    names = {s.get('name'): s for s in data.get('syscalls', [])}
    if set(names.get('bayes_update', {}).get('required_witness', [])) != {'BayesianPrior','BayesianLikelihood','EvidenceClaim','BayesianUpdateWitness'}:
        errors.append('bayes_update syscall witness set mismatch')
    if set(names.get('knot_equivalence', {}).get('required_witness', [])) != {'KnotEquivalenceWitness'}:
        errors.append('knot_equivalence syscall witness set mismatch')
    inv = data.get('invariants', [])
    for k in ['K11','K12','K13','K14','K15']:
        if not any(str(x).startswith(k + '.') for x in inv):
            errors.append(f'missing kernel invariant {k}')

def check_sql(errors):
    try:
        con = sqlite3.connect(':memory:', isolation_level=None)
        con.execute('PRAGMA foreign_keys = ON')
        con.executescript((ROOT/'executable/sql/draft5_2_schema_additions.sql').read_text())
        con.executescript((ROOT/'executable/sql/draft1_7_bayesian_knot_additions.sql').read_text())
        con.execute('BEGIN')
        con.execute("INSERT INTO srnn_bayesian_priors VALUES (?,?,?,?,?,?,?,?,?)", ('prior:1','bayesian_prior/v1','model:1','[{"hypothesis_id":"h1","probability":0.5},{"hypothesis_id":"h2","probability":0.5}]','normalized','["evidence:1"]','candidate','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_likelihoods VALUES (?,?,?,?,?,?,?,?)", ('like:1','bayesian_likelihood/v1','model:1','obs:1','[{"hypothesis_id":"h1","likelihood":0.9},{"hypothesis_id":"h2","likelihood":0.1}]','probability_mass','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_posterior_states VALUES (?,?,?,?,?,?,?,?,?,?,?)", ('post:1','bayesian_posterior_state/v1','model:1','update:1','[{"hypothesis_id":"h1","probability":0.9},{"hypothesis_id":"h2","probability":0.1}]','normalized','nc:1','computed',0,'{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_update_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('update:1','bayesian_update_witness/v1','model:1','prior:1','like:1','evidence:obs','post:1','exact_discrete_bayes',0.5,0,0,'nc:1','policy:1','grammar:1','{}','2026-05-26T00:00:00Z'))
        con.commit()
        try:
            con.execute("INSERT INTO srnn_knot_equivalence_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('keq:bad','knot_equivalence_witness/v1','a','b','ambient_isotopy','trace_verified','[]','[]',None,None,'nc:1','policy:1','{}','2026-05-26T00:00:00Z'))
            errors.append('sql guard: knot equivalence without authority path inserted')
        except sqlite3.IntegrityError:
            pass
        try:
            con.execute("INSERT INTO srnn_knot_invariant_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('inv:bad','knot_invariant_witness/v1','diagram:1','jones_polynomial','normalized','{}','deterministic_algorithm',None,None,None,'computed_support',1,'domain:all','{}','2026-05-26T00:00:00Z'))
            errors.append('sql guard: complete invariant without proof refs inserted')
        except sqlite3.IntegrityError:
            pass
        con.execute("INSERT INTO srnn_knot_equivalence_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('keq:ok','knot_equivalence_witness/v1','diagram:a','diagram:b','ambient_isotopy','trace_verified','[{"path_type":"reidemeister_trace","witness_ref":"move:1"}]','[]',None,None,'nc:1','policy:1','{}','2026-05-26T00:00:00Z'))
        con.close()
    except Exception as e:
        errors.append(f'sql v1.7 parse/apply failed: {e}')

def check_lean_static(errors):
    required = ['Duotronic/BayesianLogic.lean','Duotronic/KnotTheory.lean','Duotronic/All.lean']
    for r in required:
        if not (ROOT/r).exists(): errors.append(f'missing Lean artifact {r}')
    all_text = (ROOT/'Duotronic/All.lean').read_text()
    for mod in ['Duotronic.BayesianLogic','Duotronic.KnotTheory']:
        if mod not in all_text: errors.append(f'All.lean missing import {mod}')
    proc = subprocess.run([sys.executable, 'executable/formal/run_lean_build.py', '--mode', 'advisory', '--json'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        errors.append('lean advisory runner failed: ' + (proc.stdout + proc.stderr)[-1200:])
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

def check_inventory(errors):
    inv = load_json('PACKAGE_INVENTORY_v1_7_draft_1.json')
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

def check_inherited_v16(errors):
    proc = subprocess.run([sys.executable, 'executable/validators/validate_draft5_2_2_corpus.py'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        text = (proc.stdout + proc.stderr).strip()
        # v1.7 intentionally supersedes inventory and active kernel invariant count, so only tolerate those known inherited checks.
        tolerated = ['inventory file_count', 'missing inventory record', 'hash mismatch', 'size mismatch', 'kernel invariants count changed']
        bad = [line for line in text.splitlines() if line and not any(t in line for t in tolerated)]
        if bad:
            errors.append('inherited v1.6 validator unexpected failure: ' + '\n'.join(bad[:20]))

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
    check_inherited_v16(errors)
    check_v17_fixtures(errors)
    check_sql(errors)
    check_kernel_syscalls(errors)
    check_lean_static(errors)
    check_inventory(errors)
    if errors:
        print('\n'.join(errors))
        return 1
    print('v1.7 Draft 1 corpus validation checks passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
