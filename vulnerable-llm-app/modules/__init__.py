# Vulnerability modules for OWASP Top 10 LLM vulnerabilities

# Import all module blueprints
from . import llm01
from . import llm02
from . import llm03
from . import llm04
from . import llm05
from . import llm06
from . import llm07
from . import llm08
from . import llm09
from . import llm10

# Make blueprints available
__all__ = [
    'llm01', 'llm02', 'llm03', 'llm04', 'llm05',
    'llm06', 'llm07', 'llm08', 'llm09', 'llm10'
]
