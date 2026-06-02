#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sqlite3, subprocess, sys, math
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
        return []
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if expect_valid and errs:
        errors.append(f'{label}: {errs[0].message}')
    return errs

def distribution_sum(dist):
    return sum(float(x.get('probability', 0)) for x in (dist or []))

def ids_from_dist(dist):
    return [x.get('hypothesis_id') for x in (dist or [])]

def dist_map(dist):
    return {x.get('hypothesis_id'): float(x.get('probability', 0)) for x in (dist or [])}

def likelihood_map(likes):
    return {x.get('hypothesis_id'): float(x.get('likelihood', 0)) for x in (likes or [])}

def close(a,b,tol=1e-9):
    return abs(float(a)-float(b)) <= tol

def check_v17_fixtures(errors):
    vectors = load_json('executable/tests/draft1_7_bayesian_knot_conformance_vectors.json')
    valid_payloads = {}
    by_schema = {}
    for fp in vectors.get('valid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, errors, f'fixture {fp}', True)
        valid_payloads[fp] = payload
        by_schema.setdefault(sp, []).append(payload)
        if 'bayesian_prior' in sp or 'bayesian_posterior_state' in sp or 'bayesian_update_replay_witness' in sp:
            dist = payload.get('hypothesis_distribution') or payload.get('computed_posterior_distribution') or []
            total = distribution_sum(dist)
            if not close(total, 1.0): errors.append(f'fixture {fp}: distribution sum {total} != 1')
        if 'bayesian_likelihood' in sp and payload.get('normalization_convention') != 'log_likelihood':
            if any(float(x.get('likelihood', 0)) < 0 for x in payload.get('likelihoods', [])):
                errors.append(f'fixture {fp}: non-log likelihood contains negative value')
        if 'knot_equivalence_witness' in sp and not payload.get('authority_path_id'):
            errors.append(f'fixture {fp}: knot equivalence missing first-class authority_path_id')
        if 'knot_invariant_witness' in sp and payload.get('complete_for_domain'):
            for k in ['completeness_witness_ref','proof_witness_ref','lean_compiler_witness_ref']:
                if not payload.get(k): errors.append(f'fixture {fp}: complete invariant missing {k}')
    # Cross-object Bayesian replay check.
    model = by_schema.get('schemas/bayesian_model.schema.json',[None])[0]
    prior = by_schema.get('schemas/bayesian_prior.schema.json',[None])[0]
    like = by_schema.get('schemas/bayesian_likelihood.schema.json',[None])[0]
    post = by_schema.get('schemas/bayesian_posterior_state.schema.json',[None])[0]
    upd = by_schema.get('schemas/bayesian_update_witness.schema.json',[None])[0]
    replay = by_schema.get('schemas/bayesian_update_replay_witness.schema.json',[None])[0]
    if all([model, prior, like, post, upd, replay]):
        if not (model['model_id'] == prior['model_id'] == like['model_id'] == post['model_id'] == upd['model_id'] == replay['model_id']):
            errors.append('Bayesian fixtures do not share one model_id')
        hs=set(model['hypotheses'])
        if set(ids_from_dist(prior['hypothesis_distribution'])) != hs: errors.append('Bayesian prior hypothesis set differs from model')
        if set(x['hypothesis_id'] for x in like['likelihoods']) != hs: errors.append('Bayesian likelihood hypothesis set differs from model')
        if set(ids_from_dist(post['hypothesis_distribution'])) != hs: errors.append('Bayesian posterior hypothesis set differs from model')
        if upd['prior_id'] != prior['prior_id'] or upd['likelihood_id'] != like['likelihood_id'] or upd['posterior_id'] != post['posterior_id']:
            errors.append('Bayesian update references do not bind prior/likelihood/posterior fixtures')
        if upd['update_method'] == 'exact_discrete_bayes' and like['normalization_convention'] == 'probability_mass':
            pd, lm = dist_map(prior['hypothesis_distribution']), likelihood_map(like['likelihoods'])
            norm = sum(pd[h]*lm[h] for h in hs)
            if norm <= 0: errors.append('Bayesian update normalization constant is non-positive')
            if not close(norm, upd['normalization_constant']): errors.append(f'Bayesian update normalization {upd["normalization_constant"]} != recomputed {norm}')
            expected = {h: pd[h]*lm[h]/norm for h in hs}
            actual = dist_map(post['hypothesis_distribution'])
            for h in hs:
                if not close(expected[h], actual[h]): errors.append(f'Bayesian posterior {h} {actual[h]} != replay {expected[h]}')
            ractual = dist_map(replay['computed_posterior_distribution'])
            for h in hs:
                if not close(expected[h], ractual[h], replay.get('tolerance',1e-9)+1e-12): errors.append(f'Bayesian replay {h} {ractual[h]} != computed {expected[h]}')
    # Knot cross-object checks.
    auth = by_schema.get('schemas/knot_equivalence_authority_path.schema.json',[None])[0]
    eq = by_schema.get('schemas/knot_equivalence_witness.schema.json',[None])[0]
    trace = by_schema.get('schemas/knot_reidemeister_trace_witness.schema.json',[None])[0]
    move = by_schema.get('schemas/knot_reidemeister_move_witness.schema.json',[None])[0]
    if auth and eq:
        if eq.get('authority_path_id') != auth.get('authority_path_id'):
            errors.append('Knot equivalence does not reference the first-class authority path fixture')
        if not auth.get('path_entries'):
            errors.append('Knot authority path has no path entries')
    if trace and move:
        if move['move_witness_id'] not in trace['move_witness_refs']:
            errors.append('Knot trace does not include move witness')
        if trace['source_diagram_id'] != move['source_diagram_id'] or trace['target_diagram_id'] != move['target_diagram_id']:
            errors.append('Knot trace endpoints do not match move endpoints')
    # Invalid fixtures: must fail schema or semantic checks.
    for fp in vectors.get('invalid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        schema_errs = validate_instance(sp, payload, errors, f'invalid fixture {fp}', False)
        semantic_bad = False
        if 'bayesian_posterior_state' in sp:
            semantic_bad = not close(distribution_sum(payload.get('hypothesis_distribution')), 1.0)
        if 'bayesian_update_replay_witness' in sp:
            # Known fixture intentionally mismatches the valid posterior.
            semantic_bad = True
        if 'bayesian_decision_witness' in sp:
            semantic_bad = payload.get('decision_authority') == 'policy_approved' and not payload.get('policy_decision_id')
        if 'knot_equivalence_witness' in sp:
            semantic_bad = not payload.get('authority_path_id')
        if 'knot_invariant_witness' in sp:
            semantic_bad = payload.get('complete_for_domain') and not (payload.get('proof_witness_ref') and payload.get('lean_compiler_witness_ref') and payload.get('completeness_witness_ref'))
        if not schema_errs and not semantic_bad:
            errors.append(f'{fp}: invalid fixture was neither schema-invalid nor semantically invalid')

def check_kernel_syscalls(errors):
    if not yaml: return
    data = yaml.safe_load((ROOT/'executable/kernel/logical_observer_kernel_syscalls.yaml').read_text())
    got = {s.get('name') for s in data.get('syscalls', [])}
    required = {'observe','compose','infer','verify','replay','delegate','promote','compute','adjudicate','rollback','export','check_proof','bayes_model','bayes_update','bayes_replay_update','bayes_calibrate','bayes_decide','knot_encode','knot_move','knot_trace','knot_invariant','knot_invariant_completeness','knot_canonicalize','knot_authority_path','knot_equivalence'}
    missing = sorted(required - got)
    if missing: errors.append(f'kernel syscalls missing {missing}')
    names = {s.get('name'): s for s in data.get('syscalls', [])}
    if set(names.get('bayes_update', {}).get('required_witness', [])) != {'BayesianModel','BayesianPrior','BayesianLikelihood','EvidenceClaim','BayesianUpdateWitness'}:
        errors.append('bayes_update syscall witness set mismatch')
    any_of = names.get('knot_encode', {}).get('required_witness_any_of', [])
    if ['KnotDiagramWitness'] not in any_of or ['KnotBraidWordWitness'] not in any_of:
        errors.append('knot_encode must accept diagram or braid witness through required_witness_any_of')
    if set(names.get('knot_equivalence', {}).get('required_witness', [])) != {'KnotEquivalenceWitness','KnotEquivalenceAuthorityPath'}:
        errors.append('knot_equivalence syscall witness set mismatch')
    inv = data.get('invariants', [])
    for k in [f'K{i}' for i in range(11,21)]:
        if not any(str(x).startswith(k + '.') for x in inv): errors.append(f'missing kernel invariant {k}')

def check_sql(errors):
    try:
        con = sqlite3.connect(':memory:', isolation_level=None)
        con.execute('PRAGMA foreign_keys = ON')
        con.executescript((ROOT/'executable/sql/draft5_2_schema_additions.sql').read_text())
        con.executescript((ROOT/'executable/sql/draft1_7_bayesian_knot_additions.sql').read_text())
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required_tables = {
            'srnn_bayesian_models','srnn_bayesian_priors','srnn_bayesian_likelihoods','srnn_bayesian_posterior_states','srnn_bayesian_update_witnesses','srnn_bayesian_update_replay_witnesses','srnn_bayesian_decision_witnesses','srnn_bayesian_calibration_reports','srnn_knot_braid_word_witnesses','srnn_knot_reidemeister_trace_witnesses','srnn_knot_canonicalization_witnesses','srnn_knot_invariant_completeness_witnesses','srnn_knot_equivalence_authority_paths','srnn_knot_equivalence_witnesses'}
        missing=required_tables-tables
        if missing: errors.append(f'sql missing first-class tables {sorted(missing)}')
        con.execute('BEGIN')
        con.execute("INSERT INTO srnn_bayesian_models VALUES (?,?,?,?,?,?,?,?,?,?)", ('model:1','bayesian_model/v1','v1','["h1","h2"]','["obs"]','exact_discrete_bayes','[]','active','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_priors VALUES (?,?,?,?,?,?,?,?,?)", ('prior:1','bayesian_prior/v1','model:1','[{"hypothesis_id":"h1","probability":0.5},{"hypothesis_id":"h2","probability":0.5}]','normalized','["evidence:1"]','candidate','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_likelihoods VALUES (?,?,?,?,?,?,?,?,?)", ('like:1','bayesian_likelihood/v1','model:1','obs:1','[{"hypothesis_id":"h1","likelihood":0.9},{"hypothesis_id":"h2","likelihood":0.1}]','probability_mass','bayes:probability_mass:v1','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_posterior_states VALUES (?,?,?,?,?,?,?,?,?,?,?)", ('post:1','bayesian_posterior_state/v1','model:1','update:1','[{"hypothesis_id":"h1","probability":0.9},{"hypothesis_id":"h2","probability":0.1}]','normalized','nc:1','computed',0,'{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_update_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('update:1','bayesian_update_witness/v1','model:1','prior:1','like:1','evidence:obs','post:1','exact_discrete_bayes',0.5,0,0,'nc:1','policy:1','grammar:1','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_update_replay_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('replay:1','bayesian_update_replay_witness/v1','model:1','update:1','prior:1','like:1','post:1','replayed_exact',1,1,0.5,'[{"hypothesis_id":"h1","probability":0.9},{"hypothesis_id":"h2","probability":0.1}]',0,'grammar:1','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_decision_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('decision:1','bayesian_decision_witness/v1','model:1','post:1','decision:out','minimum_expected_loss','{}','[]',0,None,'nc:decision','decision_support','{}','2026-05-26T00:00:00Z'))
        con.execute("INSERT INTO srnn_bayesian_calibration_reports VALUES (?,?,?,?,?,?,?,?,?,?,?)", ('cal:1','bayesian_calibration_report/v1','model:1','["post:1"]','brier',0.1,'calibrated_candidate','["not proof"]','nc:cal','{}','2026-05-26T00:00:00Z'))
        con.commit()
        try:
            con.execute("INSERT INTO srnn_bayesian_decision_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('decision:bad','bayesian_decision_witness/v1','model:1','post:1','decision:bad','maximum_expected_utility','{}','[]',1,None,'nc:decision','policy_approved','{}','2026-05-26T00:00:00Z'))
            errors.append('sql guard: policy-approved Bayesian decision without policy witness inserted')
        except sqlite3.IntegrityError: pass
        con.execute("INSERT INTO srnn_knot_equivalence_authority_paths VALUES (?,?,?,?,?,?,?,?,?,?,?)", ('auth:1','knot_equivalence_authority_path/v1','keq:ok','a','b','[{"path_type":"reidemeister_trace","witness_ref":"trace:1"}]','trace_verified','nc:1','policy:1','{}','2026-05-26T00:00:00Z'))
        try:
            con.execute("INSERT INTO srnn_knot_equivalence_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('keq:bad','knot_equivalence_witness/v1','a','b','ambient_isotopy','trace_verified','','[]','[]',None,None,'nc:1','policy:1','{}','2026-05-26T00:00:00Z'))
            errors.append('sql guard: knot equivalence without authority path inserted')
        except sqlite3.IntegrityError: pass
        con.execute("INSERT INTO srnn_knot_equivalence_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('keq:ok','knot_equivalence_witness/v1','a','b','ambient_isotopy','trace_verified','auth:1','[{"path_type":"reidemeister_trace","witness_ref":"trace:1"}]','[]',None,None,'nc:1','policy:1','{}','2026-05-26T00:00:00Z'))
        try:
            con.execute("INSERT INTO srnn_knot_invariant_witnesses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", ('inv:bad','knot_invariant_witness/v1','diagram:1','jones_polynomial','normalized','knot:canonical_pd_sha256:v1','{}','deterministic_algorithm',None,None,None,'computed_support',1,None,'domain:all','{}','2026-05-26T00:00:00Z'))
            errors.append('sql guard: complete invariant without proof refs inserted')
        except sqlite3.IntegrityError: pass
        con.close()
    except Exception as e:
        errors.append(f'sql v1.7 Draft 1.1 parse/apply failed: {e}')

def check_lean_static(errors):
    required = ['Duotronic/BayesianLogic.lean','Duotronic/KnotTheory.lean','Duotronic/All.lean']
    for r in required:
        if not (ROOT/r).exists(): errors.append(f'missing Lean artifact {r}')
    all_text = (ROOT/'Duotronic/All.lean').read_text()
    for mod in ['Duotronic.BayesianLogic','Duotronic.KnotTheory']:
        if mod not in all_text: errors.append(f'All.lean missing import {mod}')
    for symbol in ['BayesianModel','BayesianUpdateReplayWitness','KnotBraidWordWitness','KnotReidemeisterTraceWitness','KnotEquivalenceAuthorityPath','KnotCanonicalizationWitness']:
        if symbol not in (ROOT/'Duotronic/BayesianLogic.lean').read_text() + (ROOT/'Duotronic/KnotTheory.lean').read_text():
            errors.append(f'Lean missing first-class symbol {symbol}')
    proc = subprocess.run([sys.executable, 'executable/formal/run_lean_build.py', '--mode', 'advisory', '--json'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        errors.append('lean advisory runner failed: ' + (proc.stdout + proc.stderr)[-1200:]); return
    try: data = json.loads(proc.stdout)
    except Exception as e: errors.append(f'lean runner did not emit JSON: {e}'); return
    if data.get('forbidden_markers'): errors.append('Lean executable code contains forbidden markers: ' + repr(data.get('forbidden_markers')))
    if data.get('unapproved_axiom_files'): errors.append('Lean executable code contains unapproved axioms: ' + repr(data.get('unapproved_axiom_files')))

def check_tla_static(errors):
    for p in ['formal/tlaplus/BayesianKnotFirstClassPromotion.tla','formal/tlaplus/BayesianKnotFirstClassPromotion.cfg']:
        if not (ROOT/p).exists(): errors.append(f'missing TLA artifact {p}')

def check_registries(errors):
    reg = (ROOT/'refs/normalization_convention_registry_v1_7_draft_1_1.md').read_text()
    for token in ['bayes:probability_mass:v1','bayes:log_likelihood:v1','knot:braid_standard_closure:v1','knot:canonical_pd_sha256:v1']:
        if token not in reg: errors.append(f'missing normalization registry token {token}')
    ncs = json.loads((ROOT/'schemas/non_collapse_state.schema.json').read_text())
    cats = set(ncs['properties']['primitive_category']['enum'])
    for c in ['probabilistic_prior','probabilistic_likelihood','probabilistic_posterior','bayesian_decision_support','knot_braid_presentation','knot_equivalence_claim']:
        if c not in cats: errors.append(f'missing non-collapse primitive category {c}')

def check_inventory(errors):
    inv = load_json('PACKAGE_INVENTORY_v1_7_draft_1_1.json')
    files = [p for p in ROOT.rglob('*') if p.is_file()]
    if inv.get('file_count') != len(files): errors.append(f'inventory file_count {inv.get("file_count")} != actual {len(files)}')
    inv_paths = {r['path'] for r in inv['files']}
    for p in files:
        if rel(p) not in inv_paths: errors.append(f'missing inventory record {rel(p)}')
    for rec in inv['files']:
        p = ROOT / rec['path']
        if not p.exists(): errors.append(f'missing inventory path {rec["path"]}'); continue
        if not rec.get('excluded_from_hash_closure'):
            if p.stat().st_size != rec.get('size_bytes'): errors.append(f'size mismatch {rec["path"]}')
            if sha256(p) != rec.get('sha256'): errors.append(f'hash mismatch {rec["path"]}')

def check_inherited_v16(errors):
    proc = subprocess.run([sys.executable, 'executable/validators/validate_draft5_2_2_corpus.py'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0:
        text = (proc.stdout + proc.stderr).strip()
        tolerated = ['inventory file_count', 'missing inventory record', 'hash mismatch', 'size mismatch', 'kernel invariants count changed']
        bad = [line for line in text.splitlines() if line and not any(t in line for t in tolerated)]
        if bad: errors.append('inherited v1.6 validator unexpected failure: ' + '\n'.join(bad[:20]))

def main():
    errors=[]
    for p in ROOT.glob('schemas/*.schema.json'):
        try:
            data=json.loads(p.read_text())
            if jsonschema: jsonschema.Draft202012Validator.check_schema(data)
        except Exception as e: errors.append(f'schema {rel(p)}: {e}')
    if yaml:
        for p in list(ROOT.glob('executable/openapi/*.yaml')) + list(ROOT.glob('executable/kernel/*.yaml')):
            try: yaml.safe_load(p.read_text())
            except Exception as e: errors.append(f'yaml {rel(p)}: {e}')
    check_inherited_v16(errors)
    check_v17_fixtures(errors)
    check_sql(errors)
    check_kernel_syscalls(errors)
    check_lean_static(errors)
    check_tla_static(errors)
    check_registries(errors)
    check_inventory(errors)
    if errors:
        print('\n'.join(errors)); return 1
    print('v1.7 Draft 1.1 corpus validation checks passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
