# LM Studio OpenWebUI Templates

These templates mirror the OWASP LLM Top 10 testing models but are adapted for use with LM Studio via OpenWebUI.

## Prerequisites
- LM Studio installed and running
- OpenAI-compatible server enabled in LM Studio (Server tab):
  - Base URL: `http://localhost:1234/v1` (default)
  - API Key: set any non-empty string (e.g., `lm-studio`) or disable key requirement
- OpenWebUI up and reachable

## Configure OpenWebUI to use LM Studio
1. In OpenWebUI Admin → Settings → Providers (or API settings):
   - Add an OpenAI-compatible provider pointing to your LM Studio server:
     - Base URL: `http://localhost:1234/v1`
     - API Key: `lm-studio` (or whatever you set in LM Studio)
2. Ensure your chosen LM Studio model is downloaded and loaded in LM Studio.

## Edit template model names
Each JSON here includes:
```
"model": "MODEL_NAME_PLACEHOLDER"
```
Replace this with your LM Studio model name (as exposed by the OpenAI server). Examples:
- `Meta-Llama-3-8B-Instruct`
- `Phi-3-mini-4k-instruct`
- `Mistral-7B-Instruct-v0.2`

Tip: You can bulk-replace `MODEL_NAME_PLACEHOLDER` across files with your preferred model.

## Import the templates
Option A – via OpenWebUI UI
1. Open OpenWebUI → Settings → Models → Import a model
2. Upload each JSON from this folder (after updating the `model` field)

Option B – via script
```
python LMStudio_openwebui_templates/import_templates_lmstudio.py --url http://<OPENWEBUI_HOST>:<PORT> --api-key <OPENWEBUI_API_KEY> --template-dir LMStudio_openwebui_templates
```

The script will test connectivity and attempt to create models using the system prompts in each template. If direct model creation endpoints aren’t available, it validates via a chat completion request.

## Included templates
- LLM01 Prompt Injection (and Jailbreak variant)
- LLM02 Insecure Output (and XSS generator variant)
- LLM03 Training Data Poisoning
- LLM04 Model Denial of Service
- LLM05 Supply Chain Compromise
- LLM06 Sensitive Info Disclosure
- LLM07 Insecure Plugin Design
- LLM08 Excessive Agency
- LLM09 Overreliance (and Overconfident Reviewer variant)
- LLM10 Model Theft
- Multimodal Injection (basic and enhanced)
- Defense Prompt Demonstration

## Notes
- These are intentionally vulnerable configurations for training and testing. Do not use in production.
- Keep LM Studio/OpenWebUI isolated from sensitive networks/data when testing.
- If a template fails to run, double-check the `model` string matches your LM Studio model name and that the provider is configured in OpenWebUI.


