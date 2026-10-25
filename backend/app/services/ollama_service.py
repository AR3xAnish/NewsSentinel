import json
import httpx
from typing import Optional, Dict, Any, List
from app.config import get_settings
from app.utils.security import guard_untrusted_content_prompt

settings = get_settings()

class OllamaService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def check_health(self) -> Dict[str, Any]:
        """
        Pings Ollama HTTP API and checks if the configured model is installed.
        Returns detailed status and friendly setup instructions if missing.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models_list = [m.get("name", "") for m in data.get("models", [])]
                    # Check if configured model or its base tag is present
                    model_found = any(
                        self.model == m or self.model in m or m.startswith(self.model.split(":")[0])
                        for m in models_list
                    )
                    
                    if model_found:
                        msg = f"Ollama is reachable and configured model '{self.model}' is installed."
                    else:
                        msg = (
                            f"Ollama is reachable, but model '{self.model}' is not installed yet. "
                            f"Run 'ollama pull {self.model}' or choose an installed model in Settings."
                        )

                    return {
                        "connected": True,
                        "base_url": self.base_url,
                        "configured_model": self.model,
                        "model_installed": model_found,
                        "available_models": models_list,
                        "message": msg,
                    }
                else:
                    return {
                        "connected": False,
                        "base_url": self.base_url,
                        "configured_model": self.model,
                        "model_installed": False,
                        "available_models": [],
                        "message": f"Ollama returned HTTP status {resp.status_code}",
                    }
        except Exception as e:
            return {
                "connected": False,
                "base_url": self.base_url,
                "configured_model": self.model,
                "model_installed": False,
                "available_models": [],
                "message": (
                    f"Could not connect to Ollama at {self.base_url}. "
                    "Make sure Ollama is installed and running locally ('ollama serve'). "
                    f"Details: {str(e)}"
                ),
            }

    async def generate_json(self, system_prompt: str, user_prompt: str, temperature: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Calls Ollama generate API asking for structured JSON output.
        Handles timeouts and malformed JSON safely.
        Never falls back to cloud models.
        """
        temp = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        payload = {
            "model": self.model,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temp,
                "num_ctx": 4096,
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                if response.status_code != 200:
                    return None

                result_json = response.json()
                raw_response_text = result_json.get("response", "").strip()

                if not raw_response_text:
                    return None

                # Clean markdown backticks if model wrapped json in ```json ... ```
                cleaned = raw_response_text
                if cleaned.startswith("```json"):
                    cleaned = cleaned[7:]
                if cleaned.startswith("```"):
                    cleaned = cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()

                return json.loads(cleaned)

        except (httpx.RequestError, json.JSONDecodeError, Exception):
            return None

    def format_untrusted_article(self, title: str, publisher: str, text: str, max_chars: int = 3500) -> str:
        """Wraps untrusted article content with prompt injection guard."""
        guarded = guard_untrusted_content_prompt(text, max_chars=max_chars)
        return f"Article Title: {title}\nPublisher: {publisher}\n\nContent:\n{guarded}"

ollama_service = OllamaService()
