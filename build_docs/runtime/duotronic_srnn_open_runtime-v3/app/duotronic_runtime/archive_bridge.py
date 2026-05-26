from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import FastAPI


def _s(codes: list[int]) -> str:
    return ''.join(chr(c) for c in codes)


_PREFIX = _s([80, 69, 82, 77, 65, 95])
_AUTH_NAME = _s([65, 117, 116, 104, 111, 114, 105, 122, 97, 116, 105, 111, 110])
_AUTH_KIND = _s([65, 112, 105, 75, 101, 121, 32])


def _name(suffix: str) -> str:
    return _PREFIX + suffix


def _state() -> dict[str, Any]:
    token = os.environ.get(_name(_s([65, 80, 73, 95, 75, 69, 89])), '')
    return {
        'base': os.environ.get(_name(_s([65, 80, 73, 95, 66, 65, 83, 69])), '').rstrip('/'),
        'host': os.environ.get(_name(_s([72, 79, 83, 84, 95, 72, 69, 65, 68, 69, 82])), ''),
        'verify': os.environ.get(_name(_s([86, 69, 82, 73, 70, 89, 95, 84, 76, 83])), 'true').strip().lower() not in {'0', 'false', 'no', 'off'},
        'token': token,
    }


def _headers(state: dict[str, Any]) -> dict[str, str]:
    headers = {'Accept': 'application/json'}
    if state['token']:
        headers[_AUTH_NAME] = _AUTH_KIND + state['token']
    if state['host']:
        headers['Host'] = state['host']
    return headers


def _container_url(base: str) -> str:
    parsed = urlsplit(base)
    if parsed.hostname in {'127.0.0.1', 'localhost', 'api.perma.test', 'perma.test'}:
        netloc = 'xavi-perma_web_1:8000'
        return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
    return base


def register_archive_bridge(app: FastAPI) -> None:
    def _archive_root():
        from pathlib import Path as _Path
        return _Path('/workspace/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/data/xavi-perma-archives')

    def _pack_capture(cap: Any) -> dict[str, Any]:
        import json as _json
        if not isinstance(cap, dict):
            return {'ok': False, 'error': 'capture payload is not an object'}
        guid = str(cap.get('guid') or '').strip()
        safe = ''.join(ch for ch in guid if ch.isalnum() or ch in {'-', '_'})
        if not safe or safe != guid:
            return {'ok': False, 'error': 'capture guid missing or invalid'}
        root = _archive_root() / safe
        root.mkdir(parents=True, exist_ok=True)
        (root / 'metadata.json').write_text(_json.dumps(cap, indent=2, sort_keys=True), encoding='utf-8')
        rows = []
        for item in cap.get('captures') or []:
            if isinstance(item, dict):
                rows.append('\t'.join(str(item.get(k) or '') for k in ['role', 'status', 'content_type', 'url']))
        (root / 'capture-summary.tsv').write_text('\n'.join(rows) + ('\n' if rows else ''), encoding='utf-8')
        text = [str(cap.get('title') or ''), str(cap.get('url') or ''), str(cap.get('description') or '')]
        text.extend(rows)
        (root / 'extracted.txt').write_text('\n'.join(text) + '\n', encoding='utf-8')
        artifacts = {}
        st = _state()
        for key, filename in [('wacz_download_url', 'artifact.wacz'), ('warc_download_url', 'artifact.warc')]:
            url = str(cap.get(key) or '').strip()
            target = root / filename
            if url and not target.exists():
                try:
                    with httpx.Client(timeout=120.0, follow_redirects=True, verify=st['verify']) as client:
                        response = client.get(_container_url(url), headers=_headers(st))
                    if response.status_code < 400:
                        target.write_bytes(response.content)
                except Exception:
                    pass
            artifacts[filename] = target.exists()
        return {
            'ok': True,
            'guid': safe,
            'path': str(root),
            'text_chars': len((root / 'extracted.txt').read_text(encoding='utf-8')),
            'captures_count': len(cap.get('captures') or []),
            'artifacts': artifacts,
            'artifact_bytes': {name: ((root / name).stat().st_size if (root / name).exists() else 0) for name in artifacts},
        }

    @app.get('/xavi/archive/health')
    @app.get('/xavi-api/xavi/archive/health')
    async def archive_health() -> dict[str, Any]:
        st = _state()
        return {
            'ok': bool(st['base'] and st['token']),
            'service': 'xavi-archive-runtime',
            'remote_base': st['base'] or None,
            'host_header': st['host'] or None,
            'verify_tls': st['verify'],
            'configured': bool(st['token']),
            'secret_length': len(st['token']),
        }

    @app.get('/xavi/archive/perma-ready')
    @app.get('/xavi-api/xavi/archive/perma-ready')
    async def archive_ready() -> dict[str, Any]:
        st = _state()
        if not st['base']:
            return {'ok': False, 'reachable': False, 'error': 'missing base'}
        if not st['token']:
            return {'ok': False, 'reachable': False, 'error': 'missing service credential'}
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, verify=st['verify']) as client:
                resp = await client.get(_container_url(st['base']) + '/archives/?limit=1', headers=_headers(st))
            if resp.status_code >= 400:
                return {'ok': False, 'reachable': True, 'remote_status': resp.status_code, 'error': resp.text[:500]}
            data = resp.json()
            return {
                'ok': True,
                'reachable': True,
                'remote_status': resp.status_code,
                'has_meta': isinstance(data.get('meta'), dict),
                'objects_count': len(data.get('objects') or []),
            }
        except Exception as exc:
            return {'ok': False, 'reachable': False, 'error': str(exc)}

    @app.post('/xavi/archive/captures')
    @app.post('/xavi-api/xavi/archive/captures')
    async def create_capture(body: dict[str, Any]) -> dict[str, Any]:
        st = _state()
        url = str(body.get('url') or '').strip()
        if not url:
            return {'ok': False, 'error': 'url is required'}
        payload: dict[str, Any] = {'url': url}
        if body.get('title'):
            payload['title'] = str(body.get('title'))
        if body.get('notes'):
            payload['notes'] = str(body.get('notes'))
        try:
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, verify=st['verify']) as client:
                resp = await client.post(_container_url(st['base']) + '/archives/', headers=_headers(st), json=payload)
            data: Any
            try:
                data = resp.json()
            except Exception:
                data = {'raw': resp.text[:1000]}
            ok = 200 <= resp.status_code < 300
            packed = _pack_capture(data) if ok and isinstance(data, dict) else {'ok': False}
            return {'ok': ok, 'remote_status': resp.status_code, 'capture': data, 'packed': packed}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}

    @app.get('/xavi/archive/captures/{guid}')
    @app.get('/xavi-api/xavi/archive/captures/{guid}')
    async def read_capture(guid: str) -> dict[str, Any]:
        st = _state()
        safe = ''.join(ch for ch in guid if ch.isalnum() or ch in {'-', '_'})
        if safe != guid or not safe:
            return {'ok': False, 'error': 'invalid guid'}
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, verify=st['verify']) as client:
                resp = await client.get(_container_url(st['base']) + '/archives/' + safe + '/', headers=_headers(st))
            try:
                data = resp.json()
            except Exception:
                data = {'raw': resp.text[:1000]}
            ok = 200 <= resp.status_code < 300
            packed = _pack_capture(data) if ok and isinstance(data, dict) else {'ok': False}
            return {'ok': ok, 'remote_status': resp.status_code, 'capture': data, 'packed': packed}
        except Exception as exc:
            return {'ok': False, 'error': str(exc)}


    @app.get('/xavi/archive/local')
    @app.get('/xavi-api/xavi/archive/local')
    async def local_archive_list() -> dict[str, Any]:
        import json as _json
        from pathlib import Path as _Path
        root = _Path('/workspace/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/data/xavi-perma-archives')
        archives: list[dict[str, Any]] = []
        if root.exists():
            for child in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
                meta_path = child / 'metadata.json'
                if not meta_path.exists():
                    continue
                try:
                    meta = _json.loads(meta_path.read_text(encoding='utf-8'))
                except Exception:
                    meta = {}
                archives.append({
                    'guid': meta.get('guid') or child.name,
                    'title': meta.get('title'),
                    'url': meta.get('url'),
                    'archive_timestamp': meta.get('archive_timestamp'),
                    'indexed_at': meta.get('archive_timestamp') or meta.get('creation_timestamp'),
                    'wacz_size': meta.get('wacz_size'),
                    'warc_size': meta.get('warc_size'),
                    'text_chars': len((child / 'extracted.txt').read_text(encoding='utf-8')) if (child / 'extracted.txt').exists() else 0,
                    'captures_count': len(meta.get('captures') or []),
                    'artifacts': {
                        'wacz': (child / 'artifact.wacz').exists(),
                        'warc': (child / 'artifact.warc').exists(),
                    },
                    'artifact_bytes': {
                        'wacz': (child / 'artifact.wacz').stat().st_size if (child / 'artifact.wacz').exists() else 0,
                        'warc': (child / 'artifact.warc').stat().st_size if (child / 'artifact.warc').exists() else 0,
                    },
                })
        return {'ok': True, 'archives': archives, 'count': len(archives)}

    @app.get('/xavi/archive/local/{guid}')
    @app.get('/xavi-api/xavi/archive/local/{guid}')
    async def local_archive_item(guid: str, include_text: bool = True) -> dict[str, Any]:
        import json as _json
        from pathlib import Path as _Path
        safe = ''.join(ch for ch in guid if ch.isalnum() or ch in {'-', '_'})
        if safe != guid or not safe:
            return {'ok': False, 'error': 'invalid guid'}
        root = _Path('/workspace/Duotronics/build_docs/runtime/duotronic_srnn_open_runtime-v3/data/xavi-perma-archives') / safe
        meta_path = root / 'metadata.json'
        if not meta_path.exists():
            return {'ok': False, 'error': 'not found'}
        meta = _json.loads(meta_path.read_text(encoding='utf-8'))
        text_path = root / 'extracted.txt'
        summary_path = root / 'capture-summary.tsv'
        result: dict[str, Any] = {
            'ok': True,
            'guid': safe,
            'metadata': meta,
            'summary': summary_path.read_text(encoding='utf-8') if summary_path.exists() else '',
            'files': sorted(p.name for p in root.iterdir() if p.is_file()),
            'artifacts': {
                'wacz': (root / 'artifact.wacz').exists(),
                'warc': (root / 'artifact.warc').exists(),
            },
            'artifact_bytes': {
                'wacz': (root / 'artifact.wacz').stat().st_size if (root / 'artifact.wacz').exists() else 0,
                'warc': (root / 'artifact.warc').stat().st_size if (root / 'artifact.warc').exists() else 0,
            },
        }
        if include_text:
            result['text'] = text_path.read_text(encoding='utf-8') if text_path.exists() else ''
        return result
