"""
Gemini Client Wrapper Module
-----------------------------
This module wraps the official Google GenAI SDK (`google-genai`).
It handles:
1. Dynamic API key initialization and verification.
2. Real-time Google Search tool grounding configuration (`tools=[types.Tool(google_search=types.GoogleSearch())]`).
3. Standard content generation and graceful error fallbacks.
"""

import os
from typing import Optional, Dict, Any, List
from config import config

# Safely import the official google-genai SDK
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    types = None

class GeminiClientWrapper:
    """
    Manages Gemini API interactions using the official google-genai SDK,
    supporting live Google Search grounding and fallback intelligence.
    """
    
    def __init__(self):
        pass

    def get_client(self) -> Optional[Any]:
        """
        Initializes and returns the GenAI Client using the active API key.
        Returns None if no key is configured or SDK is unavailable.
        """
        api_key = config.get_gemini_api_key()
        if not api_key or not GENAI_AVAILABLE:
            return None
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            print(f"[GeminiClient] Error initializing client: {e}")
            return None

    def has_valid_key(self) -> bool:
        """Checks if a Gemini API key is currently set in memory or environment."""
        return bool(config.get_gemini_api_key())

    def test_key(self, api_key: str) -> Dict[str, Any]:
        """
        Tests whether a user-provided API key is valid by sending a lightweight ping request.

        Args:
            api_key (str): The Google AI Studio API key to validate.

        Returns:
            Dict[str, Any]: {"valid": True/False, "error": Optional error string}
        """
        if not GENAI_AVAILABLE:
            return {"valid": False, "error": "google-genai package not installed."}
        try:
            client = genai.Client(api_key=api_key.strip())
            response = client.models.generate_content(
                model=config.DEFAULT_MODEL,
                contents="Ping. Respond with 'PONG'."
            )
            if response and response.text:
                return {"valid": True, "model": config.DEFAULT_MODEL}
            return {"valid": False, "error": "Empty response from Gemini"}
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def generate_with_search(self, prompt: str, system_instruction: Optional[str] = None) -> Optional[str]:
        """
        Executes generation with Google Search Grounding enabled.
        Allows Gemini to browse current scholarship portals and retrieve real-time deadlines.

        Args:
            prompt (str): User prompt / instruction.
            system_instruction (Optional[str]): Persona guidelines for the model.

        Returns:
            Optional[str]: Generated grounded response text, or None if failed.
        """
        client = self.get_client()
        if not client:
            return None
        
        try:
            # Configure live Google Search grounding tool
            cfg = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_instruction or "You are an elite master's scholarship research agent with web search access.",
                temperature=0.3
            )
            response = client.models.generate_content(
                model=config.DEFAULT_MODEL,
                contents=prompt,
                config=cfg
            )
            return response.text
        except Exception as e:
            print(f"[GeminiClient] Search-grounded generation error: {e}")
            # Try standard generation as fallback if search tool quota/access fails
            try:
                response = client.models.generate_content(
                    model=config.DEFAULT_MODEL,
                    contents=prompt
                )
                return response.text
            except Exception as e2:
                print(f"[GeminiClient] Fallback generation error: {e2}")
                return None

    def generate_text(self, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> Optional[str]:
        """
        Executes standard content generation.

        Args:
            prompt (str): Text prompt.
            system_instruction (Optional[str]): System instruction.
            json_mode (bool): If True, requests application/json MIME type.

        Returns:
            Optional[str]: Generated text response.
        """
        client = self.get_client()
        if not client:
            return None
            
        try:
            kwargs: Dict[str, Any] = {
                "system_instruction": system_instruction,
                "temperature": 0.4
            }
            if json_mode:
                kwargs["response_mime_type"] = "application/json"
                
            cfg = types.GenerateContentConfig(**kwargs)
            response = client.models.generate_content(
                model=config.DEFAULT_MODEL,
                contents=prompt,
                config=cfg
            )
            return response.text
        except Exception as e:
            print(f"[GeminiClient] Standard generation error: {e}")
            return None

# Global singleton instance of GeminiClientWrapper
gemini_client = GeminiClientWrapper()
