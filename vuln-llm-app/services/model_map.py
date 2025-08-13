from typing import Optional

# Minimal default; extend per your templates
MAP = {
    'LLM01': {
        'low': 'llm01-level1',
        'medium': 'llm01-level2',
        'high': 'llm01-level3',
        'impossible': 'llm01-level4',
        'secure': 'llm01-secure'
    }
}

def resolve_model_tag(vuln_id: Optional[str], level: Optional[str], explicit: str) -> str:
    if explicit:
        return explicit
    if not vuln_id or not level:
        return ''
    return MAP.get(vuln_id, {}).get(level, '')
