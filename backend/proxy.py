import httpx
import os
import json
from typing import Dict, Any

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def forward_to_openai(payload: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
    # Mocking for demo if no API key is provided
    if not api_key:
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "This is a mock response from SafeGate proxy. I received your request and it has been scrubbed of PII."
                }
            }],
            "usage": {
                "prompt_tokens": len(payload['messages'][0]['content']) // 4,
                "completion_tokens": 15,
                "total_tokens": (len(payload['messages'][0]['content']) // 4) + 15
            }
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(OPENAI_API_URL, json=payload, headers=headers, timeout=30.0)
        return response.json()

def calculate_cost(tokens: int, model: str = "gpt-4o"):
    # Rough estimate cost per 1k tokens
    rates = {
        "gpt-4o": 0.005 / 1000,
        "gpt-3.5-turbo": 0.001 / 1000,
        "default": 0.002 / 1000
    }
    rate = rates.get(model, rates["default"])
    return tokens * rate
