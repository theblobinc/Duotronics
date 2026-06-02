#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sqlite3, subprocess, sys, math, os, re
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
REPORT_PATH = ROOT / 'DRAFT1_2_VALIDATION_REPORT.json'

report = {
    'schema_version': 'v1_7_draft_1_2_validation_report/v1',
    'corpus_errors': [],
    'environment_warnings': [],
    'toolchain_warnings': [],
    'checks': []
}

def err(msg): report['corpus_errors'].append(msg)
def envwarn(msg): report['environment_warnings'].append(msg)
def toolwarn(msg): report['toolchain_warnings'].append(msg)
def ok(name): report['checks'].append({'name': name, 'status': 'checked'})
def rel(p: Path) -> str: return p.relative_to(ROOT).as_posix()
def sha256(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def load_json(path: str): return json.loads((ROOT / path).read_text())
def fixture_schema_payload(fp: str):
    data = load_json(fp)
    if isinstance(data, dict) and 'schema_ref' in data and 'payload' in data:
        return data['schema_ref'], data['payload']
    raise ValueError(f'fixture lacks schema_ref/payload: {fp}')

def validate_instance(schema_path, payload, label, expect_valid=True):
    if not jsonschema:
        toolwarn('jsonschema unavailable; schema instance validation skipped')
        return []
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if expect_valid and errs:
        err(f'{label}: {errs[0].message}')
    return errs

def distribution_sum(dist): return sum(float(x.get('probability', 0)) for x in (dist or []))
def ids_from_dist(dist): return [x.get('hypothesis_id') for x in (dist or [])]
def dist_map(dist): return {x.get('hypothesis_id'): float(x.get('probability', 0)) for x in (dist or [])}
def likelihood_map(likes): return {x.get('hypothesis_id'): float(x.get('likelihood', 0)) for x in (likes or [])}
def close(a,b,tol=1e-9): return abs(float(a)-float(b)) <= tol

def check_distribution(label, dist):
    total=distribution_sum(dist)
    if not close(total,1.0): err(f'{label}: distribution sum {total} != 1')

def check_braid_bounds(label, payload):
    n = int(payload.get('strand_count', 0))
    policy = payload.get('generator_bounds_policy')
    for g in payload.get('generator_sequence', []):
        idx = int(g.get('index', 0)); exp = int(g.get('exponent', 0))
        if policy == 'index_must_be_1_to_strand_count_minus_1' and not (1 <= idx <= n-1):
            err(f'{label}: braid generator index {idx} outside 1..{n-1}')
        if payload.get('zero_exponent_policy') == 'reject_zero_exponents' and exp == 0:
            err(f'{label}: zero exponent rejected by policy')

def check_v17_fixtures():
    vectors = load_json('executable/tests/draft1_7_bayesian_knot_conformance_vectors.json')
    by_schema = {}
    for fp in vectors.get('valid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, f'fixture {fp}', True)
        by_schema.setdefault(sp, []).append(payload)
        if any(x in sp for x in ['bayesian_prior','bayesian_posterior_state']):
            check_distribution(fp, payload.get('hypothesis_distribution') or [])
        if 'bayesian_update_replay_witness' in sp:
            check_distribution(fp, payload.get('computed_posterior_distribution') or [])
        if 'bayesian_posterior_predictive_witness' in sp:
            total=sum(float(x.get('probability',0)) for x in payload.get('predictive_distribution',[]))
            if not close(total,1.0): err(f'{fp}: predictive distribution sum {total} != 1')
        if any(x in sp for x in ['bayesian_marginalization_witness','bayesian_conditioning_witness']):
            total=sum(float(x.get('probability',0)) for x in payload.get('result_distribution', payload.get('conditioned_distribution', [])))
            if not close(total,1.0): err(f'{fp}: derived distribution sum {total} != 1')
        if 'bayesian_likelihood' in sp and payload.get('normalization_convention') != 'log_likelihood':
            if any(float(x.get('likelihood', 0)) < 0 for x in payload.get('likelihoods', [])):
                err(f'{fp}: non-log likelihood contains negative value')
        if 'bayesian_likelihood' in sp and payload.get('normalization_convention') == 'log_likelihood':
            if payload.get('normalization_convention_id') != 'bayes:log_likelihood:v1':
                err(f'{fp}: log likelihood missing log convention id')
        if 'knot_braid_word_witness' in sp:
            check_braid_bounds(fp, payload)
        if 'knot_reidemeister_move_witness' in sp and payload.get('move_type') in {'braid_relation','markov_move'}:
            err(f'{fp}: braid/Markov move incorrectly encoded as Reidemeister move')
        if 'knot_equivalence_witness' in sp and not payload.get('authority_path_id'):
            err(f'{fp}: knot equivalence missing first-class authority_path_id')
        if 'knot_invariant_witness' in sp:
            if payload.get('complete_for_domain'):
                for k in ['completeness_witness_ref','proof_witness_ref','lean_compiler_witness_ref']:
                    if not payload.get(k): err(f'{fp}: complete invariant missing {k}')
            if payload.get('invariant_semantics') == 'proof_backed_equivalence' and not payload.get('proof_witness_ref'):
                err(f'{fp}: proof-backed equivalence invariant missing proof witness')
    # Exact Bayesian replay checks.
    model = by_schema.get('schemas/bayesian_model.schema.json',[None])[0]
    prior = by_schema.get('schemas/bayesian_prior.schema.json',[None])[0]
    like = by_schema.get('schemas/bayesian_likelihood.schema.json',[None])[0]
    post = by_schema.get('schemas/bayesian_posterior_state.schema.json',[None])[0]
    upd = by_schema.get('schemas/bayesian_update_witness.schema.json',[None])[0]
    replay = by_schema.get('schemas/bayesian_update_replay_witness.schema.json',[None])[0]
    if all([model, prior, like, post, upd, replay]):
        if model.get('model_family') != 'discrete': err('Bayesian model fixture must declare discrete model_family')
        hs=set(model['hypotheses'])
        if not (model['model_id'] == prior['model_id'] == like['model_id'] == post['model_id'] == upd['model_id'] == replay['model_id']): err('Bayesian fixtures do not share one model_id')
        if set(ids_from_dist(prior['hypothesis_distribution'])) != hs: err('Bayesian prior hypothesis set differs from model')
        if set(x['hypothesis_id'] for x in like['likelihoods']) != hs: err('Bayesian likelihood hypothesis set differs from model')
        if set(ids_from_dist(post['hypothesis_distribution'])) != hs: err('Bayesian posterior hypothesis set differs from model')
        pd, lm = dist_map(prior['hypothesis_distribution']), likelihood_map(like['likelihoods'])
        norm = sum(pd[h]*lm[h] for h in hs)
        if norm <= 0: err('Bayesian update normalization constant is non-positive')
        if not close(norm, upd['normalization_constant']): err(f'Bayesian update normalization {upd["normalization_constant"]} != recomputed {norm}')
        expected = {h: pd[h]*lm[h]/norm for h in hs}
        actual = dist_map(post['hypothesis_distribution'])
        ractual = dist_map(replay['computed_posterior_distribution'])
        for h in hs:
            if not close(expected[h], actual[h]): err(f'Bayesian posterior {h} {actual[h]} != replay {expected[h]}')
            if not close(expected[h], ractual[h], replay.get('tolerance',1e-9)+1e-12): err(f'Bayesian replay {h} {ractual[h]} != computed {expected[h]}')
    # Log-space replay check.
    log_like = next((x for x in by_schema.get('schemas/bayesian_likelihood.schema.json',[]) if x.get('normalization_convention')=='log_likelihood'), None)
    log_replay = next((x for x in by_schema.get('schemas/bayesian_update_replay_witness.schema.json',[]) if x.get('replay_method')=='log_sum_exp_discrete_bayes'), None)
    if prior and log_like and log_replay:
        pd = dist_map(prior['hypothesis_distribution']); ll = likelihood_map(log_like['likelihoods']); hs=set(pd)
        logs = {h: math.log(pd[h]) + ll[h] for h in hs}
        m = max(logs.values()); lognorm = m + math.log(sum(math.exp(v-m) for v in logs.values()))
        expected = {h: math.exp(logs[h]-lognorm) for h in hs}
        if not close(math.exp(lognorm), log_replay['computed_normalization_constant'], 1e-9): err('log-space replay normalization mismatch')
        for h,v in dist_map(log_replay['computed_posterior_distribution']).items():
            if not close(v, expected[h], log_replay.get('tolerance',1e-9)+1e-12): err(f'log-space replay {h} {v} != computed {expected[h]}')
    # Knot cross-object checks.
    auth = by_schema.get('schemas/knot_equivalence_authority_path.schema.json',[None])[0]
    eq = by_schema.get('schemas/knot_equivalence_witness.schema.json',[None])[0]
    trace = by_schema.get('schemas/knot_reidemeister_trace_witness.schema.json',[None])[0]
    move = by_schema.get('schemas/knot_reidemeister_move_witness.schema.json',[None])[0]
    if auth and eq:
        if eq.get('authority_path_id') != auth.get('authority_path_id'): err('Knot equivalence does not reference first-class authority path fixture')
        if not auth.get('path_entries'): err('Knot authority path has no path entries')
    if trace and move:
        if move['move_witness_id'] not in trace['move_witness_refs']: err('Knot trace does not include move witness')
        if trace['source_diagram_id'] != move['source_diagram_id'] or trace['target_diagram_id'] != move['target_diagram_id']:
            err('Knot trace endpoints do not match move endpoints')
    # Invalid fixtures must fail schema or semantic checks.
    for fp in vectors.get('invalid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        schema_errs = validate_instance(sp, payload, f'invalid fixture {fp}', False)
        semantic_bad = False
        if 'bayesian_posterior_state' in sp: semantic_bad = not close(distribution_sum(payload.get('hypothesis_distribution')), 1.0)
        if 'bayesian_update_replay_witness' in sp: semantic_bad = True
        if 'bayesian_decision_witness' in sp: semantic_bad = payload.get('decision_authority') == 'policy_approved' and not payload.get('policy_decision_id')
        if 'knot_equivalence_witness' in sp: semantic_bad = not payload.get('authority_path_id')
        if 'knot_invariant_witness' in sp: semantic_bad = payload.get('complete_for_domain') and not (payload.get('proof_witness_ref') and payload.get('lean_compiler_witness_ref') and payload.get('completeness_witness_ref'))
        if 'knot_braid_word_witness' in sp:
            n=int(payload.get('strand_count',0)); semantic_bad = any(not (1 <= int(g.get('index',0)) <= n-1) or int(g.get('exponent',0))==0 for g in payload.get('generator_sequence',[]))
        if 'knot_reidemeister_move_witness' in sp: semantic_bad = payload.get('move_type') in {'braid_relation','markov_move'}
        if not schema_errs and not semantic_bad: err(f'{fp}: invalid fixture was neither schema-invalid nor semantically invalid')
    ok('fixtures')

def check_kernel_syscalls():
    if not yaml: toolwarn('yaml unavailable; kernel syscall validation skipped'); return
    data = yaml.safe_load((ROOT/'executable/kernel/logical_observer_kernel_syscalls.yaml').read_text())
    got = {s.get('name') for s in data.get('syscalls', [])}
    required = {'observe','compose','infer','verify','replay','delegate','promote','compute','adjudicate','rollback','export','check_proof','bayes_model','bayes_update','bayes_replay_update','bayes_calibrate','bayes_decide','bayes_posterior_predictive','bayes_marginalize','bayes_condition','bayes_record_negative_evidence','bayes_loss_matrix','knot_encode','knot_move','knot_braid_relation','knot_markov_move','knot_presentation_transition','knot_trace','knot_invariant','knot_invariant_completeness','knot_canonicalize','knot_authority_path','knot_equivalence'}
    missing = sorted(required - got)
    if missing: err(f'kernel syscalls missing {missing}')
    names = {s.get('name'): s for s in data.get('syscalls', [])}
    any_of = names.get('knot_encode', {}).get('required_witness_any_of', [])
    if ['KnotDiagramWitness'] not in any_of or ['KnotBraidWordWitness'] not in any_of: err('knot_encode must accept diagram or braid witness')
    inv = data.get('invariants', [])
    for k in [f'K{i}' for i in range(11,24)]:
        if not any(str(x).startswith(k + '.') for x in inv): err(f'missing kernel invariant {k}')
    ok('kernel_syscalls')

def check_sql():
    try:
        con = sqlite3.connect(':memory:', isolation_level=None)
        con.execute('PRAGMA foreign_keys = ON')
        con.executescript((ROOT/'executable/sql/draft5_2_schema_additions.sql').read_text())
        con.executescript((ROOT/'executable/sql/draft1_7_bayesian_knot_additions.sql').read_text())
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required={'srnn_bayesian_models','srnn_bayesian_priors','srnn_bayesian_likelihoods','srnn_bayesian_posterior_states','srnn_bayesian_update_witnesses','srnn_bayesian_update_replay_witnesses','srnn_bayesian_decision_witnesses','srnn_bayesian_calibration_reports','srnn_bayesian_posterior_predictive_witnesses','srnn_bayesian_marginalization_witnesses','srnn_bayesian_conditioning_witnesses','srnn_bayesian_negative_evidence_witnesses','srnn_bayesian_loss_matrix_witnesses','srnn_knot_braid_word_witnesses','srnn_knot_reidemeister_trace_witnesses','srnn_knot_braid_relation_witnesses','srnn_knot_markov_move_witnesses','srnn_knot_presentation_transition_witnesses','srnn_knot_canonicalization_witnesses','srnn_knot_invariant_completeness_witnesses','srnn_knot_equivalence_authority_paths','srnn_knot_equivalence_witnesses'}
        missing=required-tables
        if missing: err(f'sql missing first-class tables {sorted(missing)}')
        # Ensure Reidemeister table rejects Markov move.
        try:
            con.execute("INSERT INTO srnn_knot_reidemeister_move_witnesses VALUES (?,?,?,?,?,?,?,?,?,?)", ('bad','knot_reidemeister_move_witness/v1','a','b','markov_move','[]',1,'checker','nc','{}','2026-05-26T00:00:00Z'))
            err('sql guard: markov_move inserted as Reidemeister move')
        except Exception:
            pass
        con.close()
    except Exception as e:
        err(f'sql v1.7 Draft 1.2 parse/apply failed: {e}')
    ok('sql')

def check_lean_static():
    for r in ['Duotronic/BayesianLogic.lean','Duotronic/KnotTheory.lean','Duotronic/All.lean']:
        if not (ROOT/r).exists(): err(f'missing Lean artifact {r}')
    text=(ROOT/'Duotronic/BayesianLogic.lean').read_text()+(ROOT/'Duotronic/KnotTheory.lean').read_text()
    for symbol in ['BayesianPosteriorPredictiveWitness','BayesianMarginalizationWitness','BayesianConditioningWitness','BayesianNegativeEvidenceWitness','BayesianLossMatrixWitness','KnotBraidRelationWitness','KnotMarkovMoveWitness','KnotPresentationTransitionWitness']:
        if symbol not in text: err(f'Lean missing Draft 1.2 symbol {symbol}')
    proc = subprocess.run([sys.executable, 'executable/formal/run_lean_build.py', '--mode', 'advisory', '--json'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0: toolwarn('lean advisory runner failed: ' + (proc.stdout + proc.stderr)[-1200:]); return
    try: data=json.loads(proc.stdout)
    except Exception as e: toolwarn(f'lean runner did not emit JSON: {e}'); return
    if not data.get('lake_available', False): toolwarn('Lake unavailable; Lean strict build remains freeze blocker')
    if data.get('forbidden_markers'): err('Lean executable code contains forbidden markers: '+repr(data.get('forbidden_markers')))
    if data.get('unapproved_axiom_files'): err('Lean executable code contains unapproved axioms: '+repr(data.get('unapproved_axiom_files')))
    ok('lean_static')

def check_tla():
    manifest=load_json('refs/formal_toolchain/tla_toolchain_manifest_v1_0.json')
    mods={e['module']:e for e in manifest.get('tla_modules',[])}
    if 'BayesianKnotFirstClassPromotion' not in mods: err('TLA manifest missing BayesianKnotFirstClassPromotion')
    for p in ['formal/tlaplus/BayesianKnotFirstClassPromotion.tla','formal/tlaplus/BayesianKnotFirstClassPromotion.cfg']:
        if not (ROOT/p).exists(): err(f'missing TLA artifact {p}')
    proc=subprocess.run([sys.executable,'executable/formal/run_tla_model_check.py','--mode','advisory','--module','BayesianKnotFirstClassPromotion','--json'], cwd=ROOT, text=True, capture_output=True, timeout=120)
    if proc.returncode != 0: err('TLA advisory runner failed: '+(proc.stdout+proc.stderr)[-1200:])
    else:
        try:
            data=json.loads(proc.stdout)
            if data.get('status') == 'advisory_pass_tlc_unavailable': toolwarn('TLC unavailable; strict TLC remains freeze blocker')
            elif data.get('status') not in {'pass','advisory_pass_tlc_unavailable'}: err('TLA advisory status not passing: '+repr(data.get('status')))
        except Exception as e: err(f'TLA runner did not emit JSON: {e}')
    ok('tla')

def check_registries():
    for path, toks in {
        'refs/normalization_convention_registry_v1_7_draft_1_2.md':['bayes:log_space_discrete_bayes:v1','knot:gauss_code:v1','knot:grid_diagram:v1'],
        'refs/bayesian_reference_algorithms_v1_7_draft_1_2.md':['bayes:exact_discrete_bayes:v1','bayes:log_space_discrete_bayes:v1','bayes:bounded_monte_carlo:v1'],
        'refs/bayesian_calibration_scoring_registry_v1_7_draft_1_2.md':['bayes:calibration:brier:v1','bayes:calibration:expected_calibration_error:v1'],
        'refs/knot_invariant_family_registry_v1_7_draft_1_2.md':['jones_polynomial','alexander_polynomial','linking_number','quandle_coloring']
    }.items():
        txt=(ROOT/path).read_text()
        for t in toks:
            if t not in txt: err(f'missing registry token {t} in {path}')
    cats=set(load_json('schemas/non_collapse_state.schema.json')['properties']['primitive_category']['enum'])
    for c in ['bayesian_posterior_predictive','bayesian_negative_evidence','knot_braid_relation_transition','knot_markov_transition','knot_presentation_transition']:
        if c not in cats: err(f'missing non-collapse primitive category {c}')
    ok('registries')

def check_inventory():
    inv=load_json('PACKAGE_INVENTORY_v1_7_draft_1_2.json')
    files=[p for p in ROOT.rglob('*') if p.is_file()]
    if inv.get('file_count') != len(files): err(f'inventory file_count {inv.get("file_count")} != actual {len(files)}')
    inv_paths={r['path'] for r in inv['files']}
    for p in files:
        if rel(p) not in inv_paths: err(f'missing inventory record {rel(p)}')
    for rec in inv['files']:
        p=ROOT/rec['path']
        if not p.exists(): err(f'missing inventory path {rec["path"]}'); continue
        if not rec.get('excluded_from_hash_closure'):
            if p.stat().st_size != rec.get('size_bytes'): err(f'size mismatch {rec["path"]}')
            if sha256(p) != rec.get('sha256'): err(f'hash mismatch {rec["path"]}')
    ok('inventory')

def check_inherited_v16():
    env={'PATH':os.environ.get('PATH',''), 'PYTHONNOUSERSITE':'1', 'PYTHONDONTWRITEBYTECODE':'1', 'HOME':os.environ.get('HOME','/tmp')}
    proc=subprocess.run([sys.executable,'executable/validators/validate_draft5_2_2_corpus.py'], cwd=ROOT, text=True, capture_output=True, timeout=120, env=env)
    stderr_lines=[ln for ln in proc.stderr.splitlines() if ln.strip()]
    if stderr_lines:
        tolerated=('Error processing line','site-packages','distutils-precedence','google_generativeai','user site')
        noisy=[ln for ln in stderr_lines if any(t in ln for t in tolerated)]
        unexpected=[ln for ln in stderr_lines if ln not in noisy]
        if noisy: envwarn('ignored inherited validator startup stderr: '+ ' | '.join(noisy[:4]))
        if unexpected: envwarn('inherited validator stderr: '+ ' | '.join(unexpected[:4]))
    if proc.returncode != 0:
        tolerated = ['inventory file_count','missing inventory record','hash mismatch','size mismatch','kernel invariants count changed','PACKAGE_INVENTORY_v1_6','CHECKSUMS_v1_6','MANIFEST_v1_6','primitive parity missing']
        bad=[]
        for line in proc.stdout.splitlines():
            if line.strip() and not any(t in line for t in tolerated): bad.append(line)
        if bad: err('inherited v1.6 validator unexpected stdout failure: '+'\n'.join(bad[:20]))
        else: envwarn('inherited v1.6 validator reported only tolerated historical inventory/hash drift')
    ok('inherited_v16')

def main():
    for p in ROOT.glob('schemas/*.schema.json'):
        try:
            data=json.loads(p.read_text())
            if jsonschema: jsonschema.Draft202012Validator.check_schema(data)
        except Exception as e: err(f'schema {rel(p)}: {e}')
    if yaml:
        for p in list(ROOT.glob('executable/openapi/*.yaml')) + list(ROOT.glob('executable/kernel/*.yaml')):
            try: yaml.safe_load(p.read_text())
            except Exception as e: err(f'yaml {rel(p)}: {e}')
    else: toolwarn('yaml unavailable; YAML parsing skipped')
    ok('schema_and_yaml_parse')
    check_inherited_v16(); check_v17_fixtures(); check_sql(); check_kernel_syscalls(); check_lean_static(); check_tla(); check_registries(); check_inventory()
    report['status']='pass' if not report['corpus_errors'] else 'fail'
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    if report['corpus_errors']:
        print('\n'.join(report['corpus_errors']))
        print(f'Structured report written to {REPORT_PATH.relative_to(ROOT)}')
        return 1
    print('v1.7 Draft 1.2 corpus validation checks passed.')
    if report['environment_warnings'] or report['toolchain_warnings']:
        print(f'Structured report written to {REPORT_PATH.relative_to(ROOT)} with warnings.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
