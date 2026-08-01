import time
from google import genai
from google.genai import types
from config import NON_VISION_KEYWORDS, DEFAULT_MODELS

class GeminiAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key) if api_key else None

    def is_vision_model(self, model_name: str) -> bool:
        name_lower = model_name.lower()
        for keyword in NON_VISION_KEYWORDS:
            if keyword in name_lower:
                return False
        return "gemini" in name_lower

    def get_available_models(self) -> list[str]:
        if not self.client:
            return DEFAULT_MODELS
        try:
            valid_models = []
            for m in self.client.models.list():
                name = m.name.replace("models/", "") if hasattr(m, 'name') else str(m)
                if self.is_vision_model(name):
                    valid_models.append(name)
            valid_models.sort(key=lambda x: ("lite" in x, "pro" in x, "preview" in x))
            return valid_models if valid_models else DEFAULT_MODELS
        except Exception:
            return DEFAULT_MODELS

    def generate_with_fallback(
        self, 
        contents: list, 
        system_instruction: str, 
        selected_model: str
    ) -> str:
        if not self.client:
            raise ValueError("Chưa cung cấp API Key!")

        available_models = self.get_available_models()
        fallback_models = [selected_model] + [m for m in available_models if m != selected_model]
        last_exception = None

        for model_name in fallback_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1
                    )
                )
                return self._clean_output(response.text)
            except Exception as e:
                last_exception = e
                err_str = str(e)
                if any(err in err_str for err in ["400", "INVALID_ARGUMENT", "404", "NOT_FOUND"]):
                    continue
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    time.sleep(2)
                    continue
                raise e

        raise last_exception

    @staticmethod
    def _clean_output(text: str) -> str:
        clean_res = text.strip()
        if clean_res.startswith("```latex"):
            clean_res = clean_res[8:]
        if clean_res.startswith("```"):
            clean_res = clean_res[3:]
        if clean_res.endswith("```"):
            clean_res = clean_res[:-3]
        return clean_res.strip()
