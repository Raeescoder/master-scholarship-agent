import os
from typing import Optional, Dict, Any, List
from config import config

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
        api_key = config.get_gemini_api_key()
        if not api_key or not GENAI_AVAILABLE:
            return None
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            print(f"[GeminiClient] Error initializing client: {e}")
            return None

    def has_valid_key(self) -> bool:
        return bool(config.get_gemini_api_key())

    def test_key(self, api_key: str) -> Dict[str, Any]:
        if not GENAI_AVAILABLE:
            return {"valid": False, "error": "google-genai package not installed."}
        try:
            client = genai.Client(api_key=api_key.strip())
            # Quick lightweight test call
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
        Executes Gemini with live Google Search Grounding enabled.
        """
        client = self.get_client()
        if not client:
            return None
        
        try:
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
            # Try without search grounding as fallback
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
        Standard generation with optional JSON mime-type.
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

gemini_client = GeminiClientWrapper()
