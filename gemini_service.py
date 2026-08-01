# gemini_service.py
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
        if not self.client or not self.api_key:
            return DEFAULT_MODELS
        try:
            valid_models = []
            # Lấy danh sách model từ SDK google.genai
            for m in self.client.models.list():
                name = m.name.replace("models/", "") if hasattr(m, 'name') else str(m)
                if self.is_vision_model(name):
                    valid_models.append(name)
            
            if valid_models:
                valid_models.sort(key=lambda x: ("lite" in x, "pro" in x, "preview" in x))
                return valid_models
            return DEFAULT_MODELS
        except Exception:
            # Phòng trường hợp Key lỗi/chờ duyệt để UI không bị trắng mất dropdown mô hình
            return DEFAULT_MODELS

    def generate_content(
        self, 
        input_data: list = None, 
        prompt: str = "", 
        model: str = "gemini-2.5-flash",
        system_instruction: str = ""
    ) -> str:
        """
        Hàm cầu nối nhận input_data từ các Processor và chuẩn hóa nội dung 
        trước khi gọi qua hàm generate_with_fallback.
        """
        if not self.client:
            raise ValueError("Chưa cung cấp API Key!")

        contents = []

        # 1. Chuyển đổi dữ liệu binary (ảnh/PDF) từ input_data sang SDK Types Part
        if input_data:
            for item in input_data:
                file_bytes = item.get("bytes")
                mime_type = item.get("mime", "image/png")
                if file_bytes:
                    part = types.Part.from_bytes(
                        data=file_bytes,
                        mime_type=mime_type
                    )
                    contents.append(part)

        # 2. Đính kèm văn bản yêu cầu/đề toán (Prompt)
        if prompt and prompt.strip():
            contents.append(prompt)

        if not contents:
            raise ValueError("Không có nội dung dữ liệu (văn bản hoặc file) được gửi tới AI!")

        # 3. Gọi hàm xử lý chính có cơ chế Fallback
        return self.generate_with_fallback(
            contents=contents,
            system_instruction=system_instruction,
            selected_model=model
        )

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
                        system_instruction=system_instruction if system_instruction else None,
                        temperature=0.1
                    )
                )
                if response and hasattr(response, 'text') and response.text:
                    return self._clean_output(response.text)
                return ""
            except Exception as e:
                last_exception = e
                err_str = str(e)
                # Bỏ qua các lỗi liên quan đến model không tìm thấy hoặc sai argument để chuyển model dự phòng
                if any(err in err_str for err in ["400", "INVALID_ARGUMENT", "404", "NOT_FOUND", "401", "UNAUTHENTICATED"]):
                    continue
                # Nếu chạm giới hạn Rate Limit (429), nghỉ 2 giây rồi chuyển sang model tiếp theo
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    time.sleep(2)
                    continue
                raise e

        if last_exception:
            raise last_exception
        return ""

    @staticmethod
    def _clean_output(text: str) -> str:
        if not text:
            return ""
        clean_res = text.strip()
        if clean_res.startswith("```latex"):
            clean_res = clean_res[8:]
        if clean_res.startswith("```tikz"):
            clean_res = clean_res[7:]
        if clean_res.startswith("```"):
            clean_res = clean_res[3:]
        if clean_res.endswith("```"):
            clean_res = clean_res[:-3]
        return clean_res.strip()
