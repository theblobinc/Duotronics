#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'executable/runtime'))
from proof_authority import run_bounded_process

LEAN_DIRS = [ROOT / 'Duotronic', ROOT / 'formal/draft5_3_6/lean']
LEAN_ROOTS = [ROOT / 'Duotronic.lean']
STRICT_TARGETS = ['Duotronic', 'WitnessAuthority', 'witnessAuthorityInspector']

def shake256_512(path: Path) -> str:
    return hashlib.shake_256(path.read_bytes()).hexdigest(64)

def strip_comments_and_strings(src: str) -> str:
    out = []
    i = 0
    n = len(src)
    block_depth = 0
    in_line = False
    in_string = False
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ''
        if in_line:
            if c == '\n':
                in_line = False
                out.append('\n')
            else:
                out.append(' ')
            i += 1
            continue
        if block_depth > 0:
            if c == '/' and nxt == '-':
                block_depth += 1
                out.append('  ')
                i += 2
            elif c == '-' and nxt == '/':
                block_depth -= 1
                out.append('  ')
                i += 2
            else:
                out.append('\n' if c == '\n' else ' ')
                i += 1
            continue
        if in_string:
            if c == '\\':
                out.append('  ')
                i += 2
                continue
            if c == '"':
                in_string = False
            out.append(' ' if c != '\n' else '\n')
            i += 1
            continue
        if c == '-' and nxt == '-':
            in_line = True
            out.append('  ')
            i += 2
            continue
        if c == '/' and nxt == '-':
            block_depth = 1
            out.append('  ')
            i += 2
            continue
        if c == '"':
            in_string = True
            out.append(' ')
            i += 1
            continue
        out.append(c)
        i += 1
    return ''.join(out)

def lean_files() -> list[Path]:
    files = []
    for p in LEAN_ROOTS:
        if p.exists():
            files.append(p)
    for d in LEAN_DIRS:
        if d.exists():
            files.extend(sorted(d.rglob('*.lean')))
    return sorted(set(files))

def source_tree_hash(files: list[Path]) -> str:
    h = hashlib.shake_256()
    for p in sorted(files):
        h.update(p.relative_to(ROOT).as_posix().encode())
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest(64)

def static_scan(files: list[Path]) -> tuple[list[str], list[str], dict[str, list[str]]]:
    forbidden = []
    axioms = []
    theorems: dict[str, list[str]] = {}
    for p in files:
        cleaned = strip_comments_and_strings(p.read_text())
        for marker in ['sorry', 'admit']:
            if re.search(r'\b' + marker + r'\b', cleaned):
                forbidden.append(f'{p.relative_to(ROOT)}:{marker}')
        if re.search(r'^\s*axiom\b', cleaned, flags=re.M):
            axioms.append(p.relative_to(ROOT).as_posix())
        names = re.findall(r'^\s*theorem\s+([A-Za-z0-9_\.]+)', cleaned, flags=re.M)
        if names:
            theorems[p.relative_to(ROOT).as_posix()] = names
    return forbidden, axioms, theorems

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=['advisory', 'strict'], default='advisory')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    files = lean_files()
    forbidden, axioms, theorems = static_scan(files)
    lake = shutil.which('lake')
    result = {
        'schema_version': 'lean_build_result/v1',
        'mode': args.mode,
        'toolchain_file': 'lean-toolchain',
        'toolchain': (ROOT / 'lean-toolchain').read_text().strip() if (ROOT / 'lean-toolchain').exists() else None,
        'lakefile_hash': shake256_512(ROOT / 'lakefile.lean') if (ROOT / 'lakefile.lean').exists() else None,
        'source_tree_hash': source_tree_hash(files),
        'lean_files': [p.relative_to(ROOT).as_posix() for p in files],
        'forbidden_markers': forbidden,
        'unapproved_axiom_files': axioms,
        'theorems': theorems,
        'lake_available': bool(lake),
        'command': ['lake', 'build', *STRICT_TARGETS],
        'status': 'not_run',
        'stdout_tail': '',
        'stderr_tail': ''
    }
    if forbidden or axioms:
        result['status'] = 'failed_static_scan'
        code = 1
    elif lake:
        proc = run_bounded_process(tuple(result['command']), cwd=ROOT, timeout_seconds=300, env={
            'PATH': '/usr/bin:/bin', 'HOME': '/nonexistent', 'LANG': 'C.UTF-8',
            'LC_ALL': 'C.UTF-8', 'TZ': 'UTC', 'SOURCE_DATE_EPOCH': '0'
        })
        result['status'] = 'passed' if proc.returncode == 0 else 'failed_lake_build'
        result['stdout_tail'] = proc.stdout[-4000:]
        result['stderr_tail'] = proc.stderr[-4000:]
        result['output_limit_exceeded'] = proc.output_limit_exceeded
        result['timed_out'] = proc.timed_out
        if proc.output_limit_exceeded or proc.timed_out:
            result['status'] = 'failed_bounded_execution'
        code = proc.returncode or (1 if proc.output_limit_exceeded or proc.timed_out else 0)
    else:
        result['status'] = 'advisory_pass_lake_unavailable' if args.mode == 'advisory' else 'strict_fail_lake_unavailable'
        code = 0 if args.mode == 'advisory' else 2
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print('Lean build status:', result['status'])
        print('Lake available:', result['lake_available'])
    return code

if __name__ == '__main__':
    raise SystemExit(main())
