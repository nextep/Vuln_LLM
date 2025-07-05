"""
Client Registry for Vulnerable LLM Application
Provides a central registry for LLM clients that modules can import
"""

from config import LLM_BACKEND, VLLM_BASE_URL, OLLAMA_BASE_URL

# Initialize the appropriate client based on configuration
if LLM_BACKEND.lower() == 'ollama':
    from ollama_client import VulnerableOllamaClient
    llm_client = VulnerableOllamaClient(base_url=OLLAMA_BASE_URL)
else:
    from vllm_client import VulnerableLLMClient
    llm_client = VulnerableLLMClient(base_url=VLLM_BASE_URL)

# Export the client for modules to use
__all__ = ['llm_client'] 