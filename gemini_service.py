# gemini_service.py
import time
from google import genai
from google.genai import types
from config import NON_VISION_KEYWORDS, DEFAULT_MODELS

class GeminiAPIService:
    def __init__(self, api_key: str = ""):
        self._api_key = None
        self.client = None
        if api_key:
            self.api_key = api_key

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        """Mỗi khi gán/thay đổi api_key, tự động khởi tạo lại Client để nhận đủ Model"""
        cleaned_key = value.strip() if value else ""
        if self._api_key != cleaned_key:
            self._api_key = cleaned_key
            if cleaned_key:
                try:
                    self.client = genai.Client(api_key=cleaned_key)
                except Exception as e:
                    print(f"[GeminiService Debug] Lỗi khởi tạo Client: {e}")
                    self.client = None
            else:
                self.client = None

    def is_vision_model(self, model_name: str) -> bool:
        name_lower = model_name.lower()
        # Loại bỏ các model không hỗ trợ vision (như embedding, text-only cũ, ttl, etc.)
        for keyword in NON_VISION_KEYWORDS:
            if keyword in name_lower:
                return False
        return "gemini" in name_lower

    def get_available_models(self) -> list[str]:
        """Quét và lấy toàn bộ các mô hình khả dụng từ Google AI Server"""
        if not self.client:
            return DEFAULT_MODELS
            
        try:
            valid_models = []
            # Bắt toàn bộ danh sách model từ SDK mới
            models_pager = self.client.models.list()
            
            for m in models_pager:
                # Trích xuất model ID chuẩn từ SDK google-genai
                model_id = getattr(m, 'name', str(m))
                if "/" in model_id:
                    model_id = model_id.split("/")[-1]
                
                if self.is_vision_model(model_id) and model_id not in valid_models:
                    valid_models.append(model_id)
            
            if valid_models:
                # Sắp xếp ưu tiên các dòng flash, pro
                valid_models.sort(key=lambda x: ("flash" not in x, "pro" not in x, x))
                return valid_models
            
            return DEFAULT_MODELS
        except Exception as e:
            # In lỗi chi tiết ra Terminal để dễ phát hiện nguyên nhân
            print(f"[GeminiService Debug] Lỗi khi lấy danh sách model: {e}")
            return DEFAULT_MODELS

    def generate_content(
        self, 
        input_data: list = None, 
        prompt: str = "", 
        model: str = "gemini-2.5-flash",
        system_instruction: str = ""
    ) -> str:
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

                # Báo lỗi 401 ngay lập tức để người dùng kiểm tra Key
                if "401" in err_str or "UNAUTHENTICATED" in err_str:
                    raise ValueError("API Key không hợp lệ hoặc đã hết hạn! Vui lòng kiểm tra lại API Key (Key chuẩn Gemini có dạng AIzaSy...).")

                # Bỏ qua lỗi model không tìm thấy để chuyển sang model dự phòng
                if any(err in err_str for err in ["400", "INVALID_ARGUMENT", "404", "NOT_FOUND"]):
                    continue
                # Nếu chạm giới hạn Rate Limit (429), nghỉ 2 giây rồi chuyển tiếp
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
