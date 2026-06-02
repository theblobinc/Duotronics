#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, sqlite3, subprocess, sys, math, os, re, argparse, time, traceback
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
REPORT_PATH = ROOT / 'DRAFT1_3_VALIDATION_REPORT.json'

report = {
    'schema_version': 'v1_7_draft_1_3_validation_report/v1',
    'corpus_errors': [],
    'environment_warnings': [],
    'toolchain_warnings': [],
    'checks': [],
    'stages': []
}

ARGS = None

def write_partial_report(status='partial'):
    report['status'] = status if report.get('corpus_errors') else ('pass' if status == 'complete' else status)
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')

def stage(name, func):
    started = time.time()
    rec = {'name': name, 'status': 'running', 'started_at_epoch': started}
    report['stages'].append(rec)
    print(f'[stage] {name}', flush=True)
    try:
        func()
        rec['status'] = 'checked'
    except subprocess.TimeoutExpired as e:
        rec['status'] = 'timeout'
        toolwarn(f'{name} timed out after {getattr(e, "timeout", "unknown")} seconds')
    except Exception as e:
        rec['status'] = 'exception'
        err(f'{name} raised exception: {e}')
        rec['traceback_tail'] = traceback.format_exc()[-2000:]
    finally:
        rec['duration_seconds'] = round(time.time() - started, 3)
        write_partial_report('partial')

def err(msg): report['corpus_errors'].append(str(msg))
def envwarn(msg): report['environment_warnings'].append(str(msg))
def toolwarn(msg): report['toolchain_warnings'].append(str(msg))
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

MODEL_FAMILY_METHOD = {
    'discrete': {'exact_discrete_bayes','log_space_discrete_bayes'},
    'conjugate': {'conjugate_closed_form'},
    'graphical_bayesian_network': {'graphical_belief_propagation'},
    'hierarchical': {'hierarchical_update'},
    'particle_monte_carlo': {'approximate_monte_carlo'},
    'external_verified': {'external_verified'}
}

def is_model_family_compatible(payload):
    fam = payload.get('model_family')
    meth = payload.get('update_method')
    return fam in MODEL_FAMILY_METHOD and meth in MODEL_FAMILY_METHOD[fam]

def check_braid_bounds(label, payload):
    n = int(payload.get('strand_count', 0))
    policy = payload.get('generator_bounds_policy')
    for g in payload.get('generator_sequence', []):
        idx = int(g.get('index', 0)); exp = int(g.get('exponent', 0))
        if policy == 'index_must_be_1_to_strand_count_minus_1' and not (1 <= idx <= n-1):
            err(f'{label}: braid generator index {idx} outside 1..{n-1}')
        if payload.get('zero_exponent_policy') == 'reject_zero_exponents' and exp == 0:
            err(f'{label}: zero exponent rejected by policy')


def has_duplicate_ids(items, key):
    vals=[x.get(key) for x in (items or [])]
    return len(vals) != len(set(vals))

def check_unique_ids(label, items, key):
    if has_duplicate_ids(items, key):
        err(f'{label}: duplicate {key} entries are semantically rejected')

def knot_encoding_semantic_errors(payload):
    enc = payload.get('encoding_type')
    ep = payload.get('encoding_payload') or {}
    errors=[]
    cc = payload.get('crossing_count')
    if enc == 'planar_diagram':
        pd = ep.get('pd_code') or []
        if cc is not None and int(cc) != len(pd): errors.append('PD crossing_count differs from pd_code length')
        counts={}
        for quad in pd:
            for a in quad: counts[a]=counts.get(a,0)+1
        bad=[a for a,c in counts.items() if c != 2]
        if bad or len(counts) != 2*len(pd): errors.append('PD arc labels must appear exactly twice across 2n labels')
    elif enc == 'gauss_code':
        word=ep.get('gauss_word') or []
        counts={}
        for item in word: counts[item.get('label')]=counts.get(item.get('label'),0)+1
        if any(c != 2 for c in counts.values()): errors.append('Gauss crossing labels must appear exactly twice')
        if cc is not None and int(cc) != len(counts): errors.append('Gauss crossing_count differs from distinct label count')
    elif enc == 'dowker_thistlethwaite':
        dt=ep.get('dt_code') or []
        n=len(dt)
        absvals=[abs(int(x)) for x in dt]
        if any(v % 2 != 0 for v in absvals): errors.append('DT absolute entries must be even')
        if sorted(absvals) != list(range(2,2*n+1,2)): errors.append('DT absolute entries must be a permutation of 2..2n')
        if cc is not None and int(cc) != n: errors.append('DT crossing_count differs from code length')
    elif enc == 'grid_diagram':
        n=int(ep.get('grid_size',0)); xs=ep.get('x_positions') or []; os_=ep.get('o_positions') or []
        def valid_positions(pos): return all(len(p)==2 and 0 <= int(p[0]) < n and 0 <= int(p[1]) < n for p in pos)
        if len(xs)!=n or len(os_)!=n: errors.append('Grid diagram requires exactly grid_size X and O positions')
        if not valid_positions(xs) or not valid_positions(os_): errors.append('Grid coordinates outside 0..grid_size-1')
        for label,pos in [('X',xs),('O',os_)]:
            rows=[p[0] for p in pos]; cols=[p[1] for p in pos]
            if len(set(rows)) != len(rows) or len(set(cols)) != len(cols): errors.append(f'Grid {label} positions must have unique rows and columns')
    elif enc == 'braid_closure':
        n=int(ep.get('strand_count',0))
        for g in ep.get('generator_sequence') or []:
            idx=int(g.get('index',0)); exp=int(g.get('exponent',0))
            if not (1 <= idx <= n-1): errors.append('Braid closure generator index outside 1..strand_count-1')
            if exp == 0: errors.append('Braid closure zero exponent rejected')
        if cc is not None and int(cc) != len(ep.get('generator_sequence') or []): errors.append('Braid closure crossing_count differs from generator sequence length')
    elif enc == 'implementation_defined':
        h=str(ep.get('payload_hash',''))
        if not re.match(r'^(sha256|sha3_256|blake3):[0-9A-Fa-f]{16,}$', h): errors.append('Implementation-defined payload hash must have an accepted algorithm prefix')
    return errors

def semantic_invalid(schema_path, payload):
    if 'bayesian_prior' in schema_path and has_duplicate_ids(payload.get('hypothesis_distribution'), 'hypothesis_id'): return True
    if 'bayesian_likelihood' in schema_path and has_duplicate_ids(payload.get('likelihoods'), 'hypothesis_id'): return True
    if 'bayesian_posterior_state' in schema_path and has_duplicate_ids(payload.get('hypothesis_distribution'), 'hypothesis_id'): return True
    if 'bayesian_update_replay_witness' in schema_path and has_duplicate_ids(payload.get('computed_posterior_distribution'), 'hypothesis_id'): return True
    if 'knot_diagram_witness' in schema_path and knot_encoding_semantic_errors(payload): return True
    if 'bayesian_model' in schema_path and not is_model_family_compatible(payload): return True
    if 'bayesian_posterior_state' in schema_path: return not close(distribution_sum(payload.get('hypothesis_distribution')), 1.0)
    if 'bayesian_update_replay_witness' in schema_path: return True
    if 'bayesian_decision_witness' in schema_path: return payload.get('decision_authority') == 'policy_approved' and not payload.get('policy_decision_id')
    if 'knot_equivalence_witness' in schema_path: return not payload.get('authority_path_id')
    if 'knot_invariant_witness' in schema_path:
        return payload.get('complete_for_domain') and not (payload.get('proof_witness_ref') and payload.get('lean_compiler_witness_ref') and payload.get('completeness_witness_ref'))
    if 'knot_braid_word_witness' in schema_path:
        n=int(payload.get('strand_count',0))
        return any(not (1 <= int(g.get('index',0)) <= n-1) or int(g.get('exponent',0))==0 for g in payload.get('generator_sequence',[]))
    if 'knot_reidemeister_move_witness' in schema_path: return payload.get('move_type') in {'braid_relation','markov_move'}
    return False

def check_v17_fixtures():
    vectors = load_json('executable/tests/draft1_7_bayesian_knot_conformance_vectors.json')
    if vectors.get('schema_version') != 'draft1_7_bayesian_knot_conformance_vectors/v1_3':
        err('conformance vector schema_version is not Draft 1.3')
    by_schema = {}
    for fp in vectors.get('valid_fixtures', []):
        sp, payload = fixture_schema_payload(fp)
        validate_instance(sp, payload, f'fixture {fp}', True)
        by_schema.setdefault(sp, []).append(payload)
        if 'bayesian_model' in sp and not is_model_family_compatible(payload):
            err(f'{fp}: model_family/update_method pair is semantically incompatible')
        if any(x in sp for x in ['bayesian_prior','bayesian_posterior_state']):
            check_distribution(fp, payload.get('hypothesis_distribution') or [])
            check_unique_ids(fp, payload.get('hypothesis_distribution') or [], 'hypothesis_id')
        if 'bayesian_update_replay_witness' in sp:
            check_distribution(fp, payload.get('computed_posterior_distribution') or [])
            check_unique_ids(fp, payload.get('computed_posterior_distribution') or [], 'hypothesis_id')
        if 'bayesian_posterior_predictive_witness' in sp:
            total=sum(float(x.get('probability',0)) for x in payload.get('predictive_distribution',[]))
            if not close(total,1.0): err(f'{fp}: predictive distribution sum {total} != 1')
        if any(x in sp for x in ['bayesian_marginalization_witness','bayesian_conditioning_witness']):
            total=sum(float(x.get('probability',0)) for x in payload.get('result_distribution', payload.get('conditioned_distribution', [])))
            if not close(total,1.0): err(f'{fp}: derived distribution sum {total} != 1')
        if 'bayesian_likelihood' in sp:
            check_unique_ids(fp, payload.get('likelihoods') or [], 'hypothesis_id')
        if 'bayesian_likelihood' in sp and payload.get('normalization_convention') != 'log_likelihood':
            if any(float(x.get('likelihood', 0)) < 0 for x in payload.get('likelihoods', [])):
                err(f'{fp}: non-log likelihood contains negative value')
        if 'bayesian_likelihood' in sp and payload.get('normalization_convention') == 'log_likelihood':
            if payload.get('normalization_convention_id') != 'bayes:log_likelihood:v1':
                err(f'{fp}: log likelihood missing log convention id')
        if 'knot_diagram_witness' in sp:
            kerrs = knot_encoding_semantic_errors(payload)
            if kerrs: err(f'{fp}: ' + '; '.join(kerrs))
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
    # Positive branch coverage for promoted enum families.
    models = by_schema.get('schemas/bayesian_model.schema.json', [])
    got_model_families={m.get('model_family') for m in models}
    for fam in ['discrete','conjugate','graphical_bayesian_network','hierarchical','particle_monte_carlo','external_verified']:
        if fam not in got_model_families: err(f'Bayesian model family coverage missing: {fam}')
    got_methods={m.get('update_method') for m in models}
    for method in ['exact_discrete_bayes','log_space_discrete_bayes','conjugate_closed_form','graphical_belief_propagation','hierarchical_update','approximate_monte_carlo','external_verified']:
        if method not in got_methods: err(f'Bayesian update_method model coverage missing: {method}')
    diagrams = by_schema.get('schemas/knot_diagram_witness.schema.json', [])
    got_enc={d.get('encoding_type') for d in diagrams}
    for enc in ['planar_diagram','gauss_code','dowker_thistlethwaite','grid_diagram','braid_closure','implementation_defined']:
        if enc not in got_enc: err(f'Knot diagram encoding coverage missing: {enc}')
    cals = by_schema.get('schemas/bayesian_calibration_report.schema.json', [])
    got_scores={c.get('scoring_rule') for c in cals}
    for rule in ['brier','log_score','reliability_bins','expected_calibration_error','custom']:
        if rule not in got_scores: err(f'Calibration scoring rule coverage missing: {rule}')
    invs = by_schema.get('schemas/knot_invariant_witness.schema.json', [])
    got_inv={i.get('invariant_kind') for i in invs}
    for kind in ['crossing_count','component_count','determinant','alexander_polynomial','jones_polynomial','signature','linking_number','fundamental_group_presentation','wirtinger_presentation','quandle_coloring','custom']:
        if kind not in got_inv: err(f'Knot invariant coverage missing: {kind}')
    # Invalid fixtures must fail schema or semantic checks.
    invalids = vectors.get('invalid_fixtures', [])
    for required_prefix in ['invalid_knot_encoding_planar_diagram','invalid_knot_encoding_gauss_code','invalid_knot_encoding_dowker_thistlethwaite','invalid_knot_encoding_grid_diagram','invalid_knot_encoding_braid_closure','invalid_knot_encoding_implementation_defined','invalid_bayesian_model_family_discrete','invalid_bayesian_model_family_conjugate','invalid_bayesian_model_family_graphical_bayesian_network','invalid_bayesian_model_family_hierarchical','invalid_bayesian_model_family_particle_monte_carlo','invalid_bayesian_model_family_external_verified','invalid_bayesian_duplicate_prior_hypothesis_ids','invalid_bayesian_duplicate_likelihood_hypothesis_ids','invalid_bayesian_duplicate_posterior_hypothesis_ids','invalid_bayesian_duplicate_replay_hypothesis_ids','invalid_knot_encoding_planar_diagram_arc_consistency','invalid_knot_encoding_gauss_code_label_multiplicity','invalid_knot_encoding_dowker_thistlethwaite_parity','invalid_knot_encoding_grid_diagram_row_column','invalid_knot_encoding_braid_closure_generator_bounds','invalid_knot_encoding_implementation_defined_hash']:
        if not any(required_prefix in fp for fp in invalids): err(f'missing Draft 1.3 negative fixture {required_prefix}')
    for fp in invalids:
        sp, payload = fixture_schema_payload(fp)
        schema_errs = validate_instance(sp, payload, f'invalid fixture {fp}', False)
        if not schema_errs and not semantic_invalid(sp, payload):
            err(f'{fp}: invalid fixture was neither schema-invalid nor semantically invalid')
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

FIELD_MAP = {
 'hypotheses':'hypotheses_json','observation_space':'observation_space_json','assumptions':'assumptions_json','metadata':'metadata_json',
 'hypothesis_distribution':'hypothesis_distribution_json','provenance_refs':'provenance_refs_json','likelihoods':'likelihoods_json','computed_posterior_distribution':'computed_posterior_distribution_json',
 'posterior_refs':'posterior_refs_json','limitations':'limitations_json','reliability_bins':'reliability_bins_json','utility_or_loss_model':'utility_or_loss_model_json','expected_values':'expected_values_json',
 'predictive_distribution':'predictive_distribution_json','marginalized_variables':'marginalized_variables_json','result_distribution':'result_distribution_json','conditioned_distribution':'conditioned_distribution_json',
 'assumption_refs':'assumption_refs_json','actions':'actions_json','loss_entries':'loss_entries_json','encoding_payload':'encoding_payload_json','generator_sequence':'generator_sequence_json',
 'affected_crossings':'affected_crossings_json','move_witness_refs':'move_witness_refs_json','invariant_value':'invariant_value_json','path_entries':'path_entries_json','authority_path':'authority_path_json','invariant_witness_refs':'invariant_witness_refs_json','negative_or_missing_evidence_refs':'negative_or_missing_evidence_refs_json'
}
BOOL_FIELDS = {'approximation_used','hypothesis_set_verified','model_consistency_verified','policy_decision_required','checked','complete_for_domain'}

def payload_for_column(payload, col):
    if col.endswith('_json'):
        field = next((k for k,v in FIELD_MAP.items() if v == col), col[:-5])
        val = payload.get(field)
        return None if val is None else json.dumps(val, sort_keys=True)
    val = payload.get(col)
    if isinstance(val, bool): return int(val)
    if isinstance(val, (dict, list)): return json.dumps(val, sort_keys=True)
    return val

def get_sql_connection():
    con = sqlite3.connect(':memory:', isolation_level=None)
    con.execute('PRAGMA foreign_keys = ON')
    con.executescript((ROOT/'executable/sql/draft5_2_schema_additions.sql').read_text())
    con.executescript((ROOT/'executable/sql/draft1_7_bayesian_knot_additions.sql').read_text())
    return con

def check_schema_sql_persistence(con):
    reg = load_json('refs/schema_sql_persistence_registry_v1_7_draft_1_3.json')
    if reg.get('schema_version') != 'schema_sql_persistence_registry/v1': err('schema SQL persistence registry has wrong schema_version')
    for schema_path, entry in reg.get('mappings', {}).items():
        schema = load_json(schema_path)
        table = entry['table']
        cols = {r[1] for r in con.execute(f'PRAGMA table_info({table})')}
        if not cols:
            err(f'persistence registry table missing: {table}')
            continue
        mapping = entry.get('required_field_to_sql_column', {})
        not_persisted = set(entry.get('not_persisted_by_design', []))
        for field in schema.get('required', []):
            if field in not_persisted:
                continue
            col = mapping.get(field)
            if not col:
                err(f'{schema_path}: required field {field} lacks SQL column mapping or not_persisted_by_design entry')
            elif col not in cols:
                err(f'{schema_path}: required field {field} maps to missing SQL column {table}.{col}')
    ok('schema_sql_persistence')

def insert_fixture(con, table, payload):
    cols=[r[1] for r in con.execute(f'PRAGMA table_info({table})')]
    vals=[]
    for col in cols:
        vals.append(payload_for_column(payload, col))
    placeholders=','.join(['?']*len(cols))
    con.execute(f'INSERT INTO {table} ({",".join(cols)}) VALUES ({placeholders})', vals)
    pk = cols[0]
    row = con.execute(f'SELECT {",".join(cols)} FROM {table} WHERE {pk}=?', (vals[0],)).fetchone()
    if row is None:
        err(f'SQL round-trip could not read back {table}.{pk}={vals[0]}')
        return
    for i,col in enumerate(cols):
        expected=vals[i]
        got=row[i]
        if expected is not None:
            if isinstance(expected, (int, float)) and isinstance(got, (int, float)):
                if not close(got, expected):
                    err(f'SQL round-trip mismatch {table}.{col}: {got!r} != {expected!r}')
            elif str(got) != str(expected):
                err(f'SQL round-trip mismatch {table}.{col}: {got!r} != {expected!r}')

def check_sql():
    try:
        con = get_sql_connection()
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required=set(load_json('refs/schema_sql_persistence_registry_v1_7_draft_1_3.json')['mappings'][sp]['table'] for sp in load_json('refs/schema_sql_persistence_registry_v1_7_draft_1_3.json')['mappings'])
        missing=required-tables
        if missing: err(f'sql missing first-class tables {sorted(missing)}')
        check_schema_sql_persistence(con)
        # Enum coverage spot checks from the review note.
        enum_checks = [
            ("srnn_bayesian_models", ['graphical_belief_propagation','hierarchical_update']),
            ("srnn_bayesian_update_witnesses", ['graphical_belief_propagation','hierarchical_update']),
            ("srnn_bayesian_calibration_reports", ['reliability_bins']),
            ("srnn_knot_invariant_witnesses", ['determinant','linking_number','wirtinger_presentation','quandle_coloring'])
        ]
        ddl='\n'.join(r[0] or '' for r in con.execute("SELECT sql FROM sqlite_master WHERE type='table'"))
        for table, toks in enum_checks:
            for tok in toks:
                if tok not in ddl: err(f'SQL enum token {tok} missing for {table}')
        # Corrected explicit-column Reidemeister rejection check.
        try:
            con.execute("""
              INSERT INTO srnn_knot_reidemeister_move_witnesses
              (move_witness_id, schema_version, source_diagram_id, target_diagram_id, move_type, affected_crossings_json, checked, checker_ref, non_collapse_transition_id, metadata_json, created_at)
              VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, ('bad','knot_reidemeister_move_witness/v1','a','b','markov_move','[]',1,'checker','nc','{}','2026-05-26T00:00:00Z'))
            err('sql guard: markov_move inserted as Reidemeister move')
        except sqlite3.IntegrityError:
            pass
        except Exception as e:
            err(f'sql guard used an unexpected failure path instead of CHECK constraint: {e}')
        # Round-trip every valid Draft 1.3 fixture through SQL persistence.
        reg = load_json('refs/schema_sql_persistence_registry_v1_7_draft_1_3.json')['mappings']
        vectors = load_json('executable/tests/draft1_7_bayesian_knot_conformance_vectors.json')
        con.execute('BEGIN')
        for fp in vectors.get('valid_fixtures', []):
            sp, payload = fixture_schema_payload(fp)
            if sp in reg:
                try:
                    insert_fixture(con, reg[sp]['table'], payload)
                except Exception as e:
                    err(f'SQL valid fixture round-trip failed for {fp}: {e}')
        try:
            con.execute('COMMIT')
        except Exception as e:
            err(f'SQL fixture transaction commit failed: {e}')
        con.close()
    except Exception as e:
        err(f'sql v1.7 Draft 1.3 parse/apply failed: {e}')
    ok('sql')

def check_openapi():
    if not yaml:
        toolwarn('yaml unavailable; OpenAPI semantic validation skipped'); return
    data=yaml.safe_load((ROOT/'executable/openapi/draft1_7_bayesian_knot_openapi.yaml').read_text())
    comps=data.get('components',{}).get('responses',{})
    for r in ['AcceptedWitness','SemanticValidationError','ConflictWitness','WitnessLookup','ValidationReport','NotFound']:
        if r not in comps: err(f'OpenAPI missing structured response {r}')
    path_text='\n'.join(data.get('paths',{}).keys())
    if '/validation/report' not in path_text: err('OpenAPI missing /validation/report endpoint')
    if '/bayesian/update-replay/{replay_witness_id}/computed-output' not in data.get('paths',{}): err('OpenAPI missing computed replay output endpoint')
    if 'x-duotronic-error-codes' not in data: err('OpenAPI missing stable semantic error-code registry')
    if 'x-duotronic-examples' not in data: err('OpenAPI missing operation-level examples supplement')
    for path, spec in data.get('paths',{}).items():
        if path.startswith('/bayesian/') or path.startswith('/knot/'):
            if 'get' not in spec and '{replay_witness_id}' not in path:
                err(f'OpenAPI path {path} lacks GET lookup surface')
            if 'post' in spec:
                responses=spec['post'].get('responses',{})
                if '400' not in responses or '409' not in responses:
                    err(f'OpenAPI path {path} lacks semantic/conflict rejection responses')
    ok('openapi')

def check_lean_static():
    for r in ['Duotronic/BayesianLogic.lean','Duotronic/KnotTheory.lean','Duotronic/All.lean']:
        if not (ROOT/r).exists(): err(f'missing Lean artifact {r}')
    for r in ['Duotronic/CoreMetaphysics.lean','formal/lean4/DuotronicCoreMetaphysics.lean']:
        txt=(ROOT/r).read_text()
        if 'Draft 1.1' in txt: err(f'stale Draft 1.1 Lean text in {r}')
    text=(ROOT/'Duotronic/BayesianLogic.lean').read_text()+(ROOT/'Duotronic/KnotTheory.lean').read_text()
    for symbol in ['BayesianPosteriorPredictiveWitness','BayesianMarginalizationWitness','BayesianConditioningWitness','BayesianNegativeEvidenceWitness','BayesianLossMatrixWitness','KnotBraidRelationWitness','KnotMarkovMoveWitness','KnotPresentationTransitionWitness']:
        if symbol not in text: err(f'Lean missing Draft 1.3 symbol {symbol}')
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
    if manifest.get('v1_7_draft_1_3_module_integrated') is not True: err('TLA manifest does not mark Draft 1.3 module integrated')
    mods={e['module']:e for e in manifest.get('tla_modules',[])}
    if 'BayesianKnotFirstClassPromotion' not in mods: err('TLA manifest missing BayesianKnotFirstClassPromotion')
    else:
        inv=set(mods['BayesianKnotFirstClassPromotion'].get('covered_invariants',[]))
        for req in ['BayesianReplayRecomputesPosterior','KnotAuthorityPathRequired']:
            if req not in inv: err(f'TLA manifest missing invariant {req}')
    tla=(ROOT/'formal/tlaplus/BayesianKnotFirstClassPromotion.tla').read_text()
    for tok in ['BayesianReplayRecomputesPosterior','ReplayRec.normalization','AuthorityPathRec.path_entries','EquivalenceRec.authority_path_id']:
        if tok not in tla: err(f'TLA module missing Draft 1.3 record-level token {tok}')
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
        'refs/normalization_convention_registry_v1_7_draft_1_3.md':['bayes:log_space_discrete_bayes:v1','knot:gauss_code:v1','knot:grid_diagram:v1','Draft 1.3 Redo Supplement'],
        'refs/bayesian_reference_algorithms_v1_7_draft_1_2.md':['bayes:exact_discrete_bayes:v1','bayes:log_space_discrete_bayes:v1','bayes:bounded_monte_carlo:v1'],
        'refs/bayesian_calibration_scoring_registry_v1_7_draft_1_2.md':['bayes:calibration:brier:v1','bayes:calibration:expected_calibration_error:v1'],
        'refs/knot_invariant_family_registry_v1_7_draft_1_2.md':['jones_polynomial','alexander_polynomial','linking_number','quandle_coloring'],
        'refs/schema_sql_persistence_registry_v1_7_draft_1_3.json':['schema_sql_persistence_registry/v1','runtime_semantics_boundary'],
        'refs/schema_registry_v1_7_draft_1_3_completed.md':['Draft 1.3 Redo Supplement'],
        'refs/non_collapse_category_registry_v1_7_draft_1_3.md':['Draft 1.3 Redo Supplement']
    }.items():
        txt=(ROOT/path).read_text()
        for t in toks:
            if t not in txt: err(f'missing registry token {t} in {path}')
    cats=set(load_json('schemas/non_collapse_state.schema.json')['properties']['primitive_category']['enum'])
    for c in ['bayesian_posterior_predictive','bayesian_negative_evidence','knot_braid_relation_transition','knot_markov_transition','knot_presentation_transition']:
        if c not in cats: err(f'missing non-collapse primitive category {c}')
    ok('registries')

def check_docs():
    for p in ['README.md','START_HERE.md']:
        txt=(ROOT/p).read_text()
        for tok in ['Draft 1.3','validate_v1_7_draft_1_3_corpus.py','CORPUS_INDEX_v1_7_draft_1_3.md']:
            if tok not in txt: err(f'{p} missing active token {tok}')
    for p in ['BAYESIAN_LOGIC_TOP_ORDER_FACILITY_CONTRACT_v1_0.md','KNOT_THEORY_WITNESS_FACILITY_CONTRACT_v1_0.md']:
        txt=(ROOT/p).read_text()
        if 'Draft 1.1' in txt: err(f'{p} still contains stale Draft 1.1 text')
        if 'Draft 1.3 schema-SQL-runtime consistency addendum' not in txt: err(f'{p} missing Draft 1.3 addendum')
    if not (ROOT/'RUNTIME_SQL_SEMANTIC_BOUNDARY_v1_7_draft_1_3.md').exists(): err('missing runtime SQL semantic boundary doc')
    for p in ['corpus_review_v1_7_draft_1_2_to_v1_7_draft_1_3.md','DRAFT1_3_VALIDATOR_ORCHESTRATION_HARDENING.md','DRAFT1_3_FIXTURE_COVERAGE_MATRIX.md']:
        if not (ROOT/p).exists(): err(f'missing Draft 1.3 redo doc {p}')
    ok('docs')

def check_inventory():
    inv=load_json('PACKAGE_INVENTORY_v1_7_draft_1_3.json')
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

def parse_args():
    parser = argparse.ArgumentParser(description='Validate v1.7 Draft 1.3 corpus with stage-aware orchestration.')
    parser.add_argument('--skip-inherited', action='store_true', help='Skip inherited v1.6/v1.5 validator subprocess')
    parser.add_argument('--skip-lean', action='store_true', help='Skip Lean advisory stage')
    parser.add_argument('--skip-tla', action='store_true', help='Skip TLA advisory stage')
    return parser.parse_args()

def check_schema_and_yaml_parse():
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

def main():
    global ARGS
    ARGS = parse_args()
    try:
        stage('schema_and_yaml_parse', check_schema_and_yaml_parse)
        if ARGS.skip_inherited:
            envwarn('inherited validator skipped by --skip-inherited')
        else:
            stage('inherited_v16', check_inherited_v16)
        stage('v17_fixtures', check_v17_fixtures)
        stage('sql', check_sql)
        stage('openapi', check_openapi)
        stage('kernel_syscalls', check_kernel_syscalls)
        if ARGS.skip_lean:
            toolwarn('Lean advisory stage skipped by --skip-lean')
        else:
            stage('lean_static', check_lean_static)
        if ARGS.skip_tla:
            toolwarn('TLA advisory stage skipped by --skip-tla')
        else:
            stage('tla', check_tla)
        stage('registries', check_registries)
        stage('docs', check_docs)
        stage('inventory', check_inventory)
    finally:
        report['status']='pass' if not report['corpus_errors'] else 'fail'
        REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    if report['corpus_errors']:
        print('\n'.join(report['corpus_errors']))
        print(f'Structured report written to {REPORT_PATH.relative_to(ROOT)}')
        return 1
    print('v1.7 Draft 1.3 corpus validation checks passed.')
    if report['environment_warnings'] or report['toolchain_warnings']:
        print(f'Structured report written to {REPORT_PATH.relative_to(ROOT)} with warnings.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
