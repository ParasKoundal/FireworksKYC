"""
Debug script to test Fireworks AI API connectivity and model availability.
Tests both the Chat Completions API and the Completions API for vision models.
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("FIREWORKS_API_KEY")
chat_url = "https://api.fireworks.ai/inference/v1/chat/completions"
completions_url = "https://api.fireworks.ai/inference/v1/completions"

# First, fetch available vision models from the API
print("=" * 60)
print("FIREWORKS AI API DEBUG")
print("=" * 60)
print(f"API Key: {'*' * 10}{api_key[-4:] if api_key else 'NOT SET'}")
print()

print("Fetching available models...")
models_url = "https://api.fireworks.ai/inference/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

try:
    response = requests.get(models_url, headers=headers, timeout=30)
    if response.status_code == 200:
        all_models = response.json().get("data", [])
        vision_models = [m["id"] for m in all_models if "vl" in m.get("id", "").lower() or "vision" in m.get("id", "").lower()]
        print(f"Found {len(vision_models)} accessible vision models:")
        for m in vision_models:
            print(f"  - {m}")
    else:
        print(f"Could not fetch models: {response.status_code}")
        vision_models = []
except Exception as e:
    print(f"Error fetching models: {e}")
    vision_models = []

# Test each available vision model
models_to_test = vision_models[:3] if vision_models else [
    "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
]

# Simple test image URL
image_url = "https://images.unsplash.com/photo-1582538885592-e70a5d7ab3d3?ixlib=rb-4.0.3&w=400"

for model in models_to_test:
    print(f"\n{'=' * 60}")
    print(f"Testing Model: {model}")
    print("=" * 60)
    
    # Test 1: Chat Completions API (recommended for vision)
    print("\n--- Test 1: Chat Completions API ---")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url
                        }
                    },
                    {
                        "type": "text",
                        "text": "What is in this image? Reply in one sentence."
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(chat_url, headers=headers, json=payload, timeout=120)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            error = response.json().get('error', {}).get('message', response.text)
            print(f"Error: {error}")
        else:
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
            print(f"Success! Response: {content[:200]}...")
    except Exception as e:
        print(f"Exception: {str(e)}")

    # Test 2: Completions API with <image> token
    print("\n--- Test 2: Completions API with <image> token ---")
    payload = {
        "model": model,
        "prompt": "<image>\nWhat is in this image? Reply in one sentence.",
        "images": [image_url],
        "temperature": 0.1,
        "max_tokens": 50
    }
    
    try:
        response = requests.post(completions_url, headers=headers, json=payload, timeout=120)
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            error = response.json().get('error', {}).get('message', response.text)
            print(f"Error: {error}")
        else:
            result = response.json()
            text = result.get('choices', [{}])[0].get('text', 'No text')
            print(f"Success! Response: {text[:200]}...")
    except Exception as e:
        print(f"Exception: {str(e)}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)
