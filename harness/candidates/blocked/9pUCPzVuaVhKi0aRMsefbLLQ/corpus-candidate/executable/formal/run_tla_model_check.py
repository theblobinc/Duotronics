#!/usr/bin/env python3
"""Run canonical Draft 5.3.4 TLA+ model checks from the strict manifest.

Modes:
- advisory: perform portable manifest/config/static checks; run TLC if available; pass if TLC is absent.
- strict: require TLC and fail on any unavailable tool or nonzero TLC result.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'refs/formal_toolchain/tla_toolchain_manifest_v1_0.json'


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def locate_tlc() -> Path | None:
    env = os.environ.get('TLA2TOOLS_JAR')
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(ROOT / 'tools/tla2tools.jar')
    candidates.append(ROOT / 'tools/tla2tools-1.8.0.jar')
    for p in candidates:
        if p.exists() and p.is_file():
            return p
    return None


def parse_cfg_invariants(cfg_text: str) -> list[str]:
    lines = cfg_text.splitlines()
    invariants: list[str] = []
    in_block = False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith('\\*'):
            continue
        if line == 'INVARIANTS':
            in_block = True
            continue
        if in_block and re.match(r'^[A-Z][A-Z_]+\b', line):
            break
        if in_block:
            invariants.append(line.split()[0])
    return invariants


def static_check_module(entry: dict) -> list[str]:
    errors: list[str] = []
    module = entry['module']
    spec_path = ROOT / entry['spec']
    cfg_path = ROOT / entry['config']
    if not spec_path.exists():
        return [f'{module}: missing spec {entry["spec"]}']
    if not cfg_path.exists():
        return [f'{module}: missing config {entry["config"]}']
    spec_text = spec_path.read_text()
    cfg_text = cfg_path.read_text()
    if f'MODULE {module}' not in spec_text:
        errors.append(f'{module}: module header mismatch')
    if '====' not in spec_text:
        errors.append(f'{module}: missing TLA module footer')
    if 'Spec ==' not in spec_text:
        errors.append(f'{module}: missing Spec operator')
    if 'SPECIFICATION Spec' not in cfg_text:
        errors.append(f'{module}: cfg missing SPECIFICATION Spec')
    cfg_invariants = parse_cfg_invariants(cfg_text)
    if not cfg_invariants:
        errors.append(f'{module}: cfg has no INVARIANTS block')
    for inv in cfg_invariants:
        if f'{inv} ==' not in spec_text:
            errors.append(f'{module}: invariant {inv} listed in cfg but not defined in spec')
    for inv in entry.get('covered_invariants', []):
        if inv not in cfg_invariants:
            errors.append(f'{module}: manifest invariant {inv} missing from cfg')
    if "Seq(Claims)" in spec_text:
        errors.append(f'{module}: unbounded Seq(Claims) detected; use bounded premise sequences')
    if 'CHOOSE c \\in Capabilities : TRUE' in spec_text and 'Capabilities = {}' in cfg_text:
        errors.append(f'{module}: empty capability set would break CHOOSE')
    return errors


def run_tlc(jar: Path, entry: dict, timeout: int) -> dict:
    cfg_path = ROOT / entry['config']
    module_path = ROOT / entry['spec']
    cmd = [
        'java', '-cp', str(jar), 'tlc2.TLC',
        '-deadlock',
        '-config', str(cfg_path.name),
        module_path.stem,
    ]
    proc = subprocess.run(
        cmd,
        cwd=module_path.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return {
        'module': entry['module'],
        'return_code': proc.returncode,
        'command': ' '.join(cmd),
        'output_tail': proc.stdout[-4000:],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['advisory', 'strict'], default='advisory')
    ap.add_argument('--module', default='all')
    ap.add_argument('--timeout', type=int, default=60)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    manifest = load_manifest()
    entries = manifest['tla_modules']
    if args.module != 'all':
        entries = [e for e in entries if e['module'] == args.module]
        if not entries:
            print(f'Unknown TLA module: {args.module}', file=sys.stderr)
            return 2

    static_errors: list[str] = []
    for entry in entries:
        static_errors.extend(static_check_module(entry))

    jar = locate_tlc()
    tlc_results: list[dict] = []
    if jar:
        for entry in entries:
            try:
                tlc_results.append(run_tlc(jar, entry, args.timeout))
            except subprocess.TimeoutExpired:
                tlc_results.append({
                    'module': entry['module'],
                    'return_code': 124,
                    'command': 'timeout',
                    'output_tail': f'TLC timed out after {args.timeout} seconds',
                })
    elif args.mode == 'strict':
        static_errors.append('TLC unavailable: set TLA2TOOLS_JAR or place tools/tla2tools.jar under corpus root')

    tlc_failures = [r for r in tlc_results if r['return_code'] != 0]
    status = 'pass' if not static_errors and not tlc_failures else 'fail'
    if not jar and args.mode == 'advisory' and status == 'pass':
        status = 'advisory_pass_tlc_unavailable'

    result = {
        'schema_version': 'tla_model_check_result/v1',
        'mode': args.mode,
        'status': status,
        'tlc_available': jar is not None,
        'tlc_jar': str(jar) if jar else None,
        'modules_checked': [e['module'] for e in entries],
        'static_errors': static_errors,
        'tlc_results': tlc_results,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f'Draft 5.3.4 TLA+ validation status: {status}')
        print(f'TLC available: {jar is not None}')
        for err in static_errors:
            print(f'ERROR: {err}')
        for r in tlc_results:
            print(f'{r["module"]}: TLC return code {r["return_code"]}')
            if r['return_code'] != 0:
                print(r['output_tail'])
    return 0 if status in {'pass', 'advisory_pass_tlc_unavailable'} else 1


if __name__ == '__main__':
    raise SystemExit(main())
