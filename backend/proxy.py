import os
import json
import google.generativeai as genai
from typing import Dict, Any

def forward_to_gemini(payload: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
    # 1. Handle Mock Mode if no API key
    if not api_key:
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "This is a MOCK response from SafeGate (Google Gemini Mode). I received your request and it has been scrubbed of PII."
                }
            }],
            "usage": {
                "prompt_tokens": len(payload['messages'][0]['content']) // 4,
                "completion_tokens": 15,
                "total_tokens": (len(payload['messages'][0]['content']) // 4) + 15
            }
        }

    # 2. Configure Gemini
    genai.configure(api_key=api_key)
    model_name = payload.get("model", "gemini-1.5-flash")
    
    # Ensure model starts with "models/" prefix
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
    
    try:
        model = genai.GenerativeModel(model_name)
        
        # 3. Get the scrubbed message
        user_message = payload['messages'][-1]['content']
        
        # 4. Generate Response
        response = model.generate_content(user_message)
        
        # 5. Format to match OpenAI style (so frontend/app.py doesn't break)
        prompt_tokens = len(user_message) // 4
        completion_tokens = len(response.text) // 4
        
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response.text
                }
            }],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens
            }
        }
    except Exception as e:
        # If model fails, try listing models to see what's available
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        raise Exception(f"Gemini API Error: {str(e)}. Available models for your key: {available_models}")

async def forward_to_openai(payload: Dict[str, Any], api_key: str = None) -> Dict[str, Any]:
    # We will redirect this to Gemini for your convenience
    return forward_to_gemini(payload, api_key)

def calculate_cost(tokens: int, model: str = "gemini-2.0-flash"):
    # Gemini 2.0 Flash is currently in preview/free tier
    rates = {
        "gemini-2.0-flash": 0.0,
        "gemini-1.5-flash": 0.0,
        "gemini-1.5-pro": 0.001 / 1000,
        "default": 0.0005 / 1000
    }
    rate = rates.get(model, rates["default"])
    return tokens * rate
