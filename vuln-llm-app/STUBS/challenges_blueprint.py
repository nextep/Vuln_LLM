from flask import Blueprint, render_template, request, jsonify
from typing import Dict, Any
from GPT5.STUBS.evaluators import evaluate
from GPT5.STUBS.anti_cheat import RateLimiter

# Using existing client via registry
from client_registry import llm_client
from config import DIFFICULTY_MODEL_MAP
import json
import os

bp = Blueprint('challenges', __name__)
_limiter = RateLimiter()


def _load_manifest() -> Any:
    # Try local working dir first (app runs from vulnerable-llm-app/)
    for candidate in [
        'test_cases.json',
        os.path.join('vulnerable-llm-app', 'test_cases.json'),
        os.path.join(os.getcwd(), 'test_cases.json'),
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
                    # Attach resolved meta
                    t['_level'] = level_name
                    t['_model_tag'] = level.get('model_tag')
                    t['_vuln_id'] = vuln.get('id')
                    return t
    return {}


def _resolve_model_tag(vuln_id: str, level: str, explicit: str) -> str:
    if explicit:
        return explicit
    vid = (vuln_id or '').upper()
    lvl = (level or '').lower()
    mapping = DIFFICULTY_MODEL_MAP.get(vid, {}) or DIFFICULTY_MODEL_MAP.get(vid.replace('LLM', 'LLM'), {})
    return mapping.get(lvl, '')


@bp.route('/')
def catalog() -> Any:
    data = _load_manifest()
    return render_template('challenges/catalog.html', data=data)


@bp.route('/<challenge_id>')
def detail(challenge_id: str) -> Any:
    test = _find_test(challenge_id)
    if not test:
        return render_template('challenges/detail.html', test={'id': challenge_id, 'name': 'Unknown Challenge'}), 404
    return render_template('challenges/detail.html', test=test)


@bp.route('/<challenge_id>/attempt', methods=['POST'])
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

    model_tag = _resolve_model_tag(test_case.get('_vuln_id'), test_case.get('_level'), (test_case.get('_model_tag') or '').strip())
    if not model_tag:
        return jsonify({'error': 'Challenge misconfigured (no model_tag for this level)'}), 500

    # Server-side call to OpenWebUI
    result = llm_client.call_vulnerable_model(
        model_tag=model_tag,
        user_prompt=payload,
        use_system_prompt=True
    )

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