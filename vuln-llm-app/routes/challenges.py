from flask import Blueprint, render_template, request, jsonify
from typing import Dict, Any
import json
import os

from services.evaluators import evaluate
from services.anti_cheat import RateLimiter
from services.openwebui import OpenWebUI
from services.model_map import resolve_model_tag

bp = Blueprint('gpt5_challenges', __name__)
_limiter = RateLimiter()
_owui = OpenWebUI()


def _load_manifest() -> Any:
    for candidate in [
        os.path.join(os.path.dirname(__file__), '..', 'test_cases.json'),
        os.path.join(os.getcwd(), 'vulnerable-llm-app', 'test_cases.json'),
        os.path.join(os.getcwd(), 'test_cases.json'),
        os.path.join(os.getcwd(), 'Keep', 'openwebui_templates', 'test_cases.json'),
    ]:
        try:
            with open(candidate, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            continue
    return { 'vulnerabilities': [] }


def _find_test(challenge_id: str) -> Dict[str, Any]:
    data = _load_manifest()
    for vuln in data.get('vulnerabilities', []):
        for level_name, level in (vuln.get('levels') or {}).items():
            for t in (level.get('tests') or []):
                if t.get('id') == challenge_id:
                    t['_level'] = level_name
                    t['_model_tag'] = level.get('model_tag')
                    t['_vuln_id'] = vuln.get('id')
                    return t
    return {}


@bp.route('/')
@bp.route('/challenges')
def catalog() -> Any:
    data = _load_manifest()
    return render_template('challenges/catalog.html', data=data)


@bp.route('/challenge/<challenge_id>')
def detail(challenge_id: str) -> Any:
    test = _find_test(challenge_id)
    if not test:
        return render_template('challenges/detail.html', test={'id': challenge_id, 'name': 'Unknown Challenge'}), 404
    return render_template('challenges/detail.html', test=test)


@bp.route('/challenge/<challenge_id>/attempt', methods=['POST'])
def attempt(challenge_id: str) -> Dict[str, Any]:
    user_key = request.remote_addr or 'anon'
    if not _limiter.allow(f"attempt:{user_key}"):
        return jsonify({'error': 'Rate limit exceeded'}), 429

    payload = request.form.get('payload', '').strip()
    if not payload:
        return jsonify({'error': 'Missing payload'}), 400

    test_case = _find_test(challenge_id)
    if not test_case:
        return jsonify({'error': 'Invalid challenge id'}), 400

    model_tag = resolve_model_tag(test_case.get('_vuln_id'), test_case.get('_level'), (test_case.get('_model_tag') or '').strip())
    if not model_tag:
        return jsonify({'error': 'Challenge misconfigured (no model_tag for this level)'}), 500

    result = _owui.complete(model_tag=model_tag, user_prompt=payload)
    if result.get('error'):
        return jsonify({'error': result.get('error')}), 502

    response_text = result.get('response', '')
    score, feedback, indicators = evaluate(challenge_id, payload, response_text)

    return jsonify({
        'score': score,
        'feedback': feedback,
        'indicators': indicators,
        'response_time': result.get('response_time', 0)
    })
