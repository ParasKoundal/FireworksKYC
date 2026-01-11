"""
Fireworks AI API client for vision-language model interactions.
"""
import os
import base64
import json
from typing import Optional, Union
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()


class FireworksClient:
    """Client for interacting with Fireworks AI vision-language models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "accounts/fireworks/models/qwen2p5-vl-32b-instruct",
        base_url: str = "https://api.fireworks.ai/inference/v1"
    ):
        """
        Initialize Fireworks AI client.

        Args:
            api_key: Fireworks API key (defaults to FIREWORKS_API_KEY env var)
            model: Model identifier to use for vision tasks
            base_url: Base URL for Fireworks API
        """
        self.api_key = api_key or os.getenv("FIREWORKS_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Fireworks API key required. Set FIREWORKS_API_KEY environment variable "
                "or pass api_key parameter."
            )

        # Normalize model name to full path format
        if not model.startswith("accounts/"):
            model = f"accounts/fireworks/models/{model}"
        
        self.model = model
        self.base_url = base_url
        # Use Chat Completions API for vision models (more reliable)
        self.chat_endpoint = f"{base_url}/chat/completions"
        self.completions_endpoint = f"{base_url}/completions"

    def encode_image(self, image_path: Union[str, Path]) -> str:
        """
        Encode image file to base64 data URI.

        Args:
            image_path: Path to image file

        Returns:
            Base64 encoded data URI string
        """
        image_path = Path(image_path)

        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Determine MIME type from extension
        extension = image_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }

        mime_type = mime_types.get(extension, "image/jpeg")

        # Read and encode image
        with open(image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")

        return f"data:{mime_type};base64,{encoded}"

    def analyze_document(
        self,
        image_path: Union[str, Path],
        prompt: str,
        response_format: Optional[dict] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> dict:
        """
        Analyze a document image using vision-language model.
        
        Uses the Chat Completions API which is more reliable for vision models.

        Args:
            image_path: Path to document image
            prompt: Text prompt for analysis
            response_format: Optional response format specification
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            API response dictionary
        """
        # Encode image
        image_data_uri = self.encode_image(image_path)

        # Build message content with image and text
        # Image should come before text for best results with vision models
        content = [
            {
                "type": "image_url",
                "image_url": {
                    "url": image_data_uri
                }
            },
            {
                "type": "text",
                "text": prompt
            }
        ]

        # Construct Chat Completions API request
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1,
        }

        # Add response format if specified (for JSON mode)
        if response_format:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Make request to Chat Completions endpoint
        response = requests.post(
            self.chat_endpoint,
            headers=headers,
            json=payload,
            timeout=120  # Increased timeout for vision models
        )

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", response.text)
            except:
                pass
            raise RuntimeError(f"Fireworks API Error ({response.status_code}): {error_detail}")

        return response.json()

    def analyze_document_completions(
        self,
        image_path: Union[str, Path],
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> dict:
        """
        Analyze a document image using the Completions API (fallback method).
        
        Note: Requires <image> token in prompt to match number of images.

        Args:
            image_path: Path to document image
            prompt: Text prompt for analysis (without <image> token - will be added)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            API response dictionary
        """
        # Encode image
        image_data_uri = self.encode_image(image_path)

        # Add <image> token at the start of the prompt to match the image
        # This is required by the Completions API for vision models
        prompt_with_token = f"<image>\n{prompt}"

        # Construct Completions API request
        payload = {
            "model": self.model,
            "prompt": prompt_with_token,
            "images": [image_data_uri],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 1,
            "top_k": 40
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Make request
        response = requests.post(
            self.completions_endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("error", {}).get("message", response.text)
            except:
                pass
            raise RuntimeError(f"Fireworks API Error ({response.status_code}): {error_detail}")

        return response.json()

    def extract_structured_data(
        self,
        image_path: Union[str, Path],
        json_schema: dict,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> dict:
        """
        Extract structured data from document using JSON schema.

        Args:
            image_path: Path to document image
            json_schema: JSON schema defining expected output structure
            prompt: Text prompt for extraction
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response

        Returns:
            Extracted structured data
        """
        # Try with JSON response format first
        try:
            response_format = {
                "type": "json_object"
            }

            response = self.analyze_document(
                image_path=image_path,
                prompt=prompt,
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except RuntimeError as e:
            # If response_format is not supported, try without it
            if "response_format" in str(e).lower() or "400" in str(e):
                response = self.analyze_document(
                    image_path=image_path,
                    prompt=prompt,
                    response_format=None,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                raise

        # Extract the content from response
        # Chat API uses ["message"]["content"], Completions API uses ["text"]
        if "message" in response["choices"][0]:
            content = response["choices"][0]["message"]["content"]
        else:
            content = response["choices"][0]["text"]

        # Parse JSON if returned as string
        if isinstance(content, str):
            # Clean up potential markdown formatting (```json ... ```)
            content = content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            elif content.startswith("```"):
                parts = content.split("```")
                if len(parts) >= 2:
                    content = parts[1].strip()
                    # Remove language identifier if present (e.g., "json\n{...}")
                    if content.startswith("json"):
                        content = content[4:].strip()
                
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try to find JSON object in the content
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                # If it's not JSON, return the raw content
                return {"raw_text": content}

        return content
