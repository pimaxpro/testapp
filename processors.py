from abc import ABC, abstractmethod
from google.genai import types
from gemini_service import GeminiAPIService
from config import PROMPTS

class BaseProcessor(ABC):
    def __init__(self, api_service: GeminiAPIService):
        self.api_service = api_service

    @abstractmethod
    def process(self, file_bytes: bytes, mime_type: str, model: str, extra_prompt: str) -> str:
        pass


class ExTestProcessor(BaseProcessor):
    """Chức năng 1: Chuyển Ảnh/PDF đề thi sang ex_test"""
    def process(self, file_bytes: bytes, mime_type: str, model: str, extra_prompt: str) -> str:
        prompt = "Hãy nhận diện toàn bộ tài liệu này và chuyển thành mã LaTeX theo chuẩn gói ex_test."
        sys_prompt = PROMPTS["EX_TEST"]
        if extra_prompt.strip():
            sys_prompt += f"\nYêu cầu bổ sung: {extra_prompt.strip()}"

        contents = [
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            prompt
        ]
        return self.api_service.generate_with_fallback(contents, sys_prompt, model)


class TikZProcessor(BaseProcessor):
    """Chức năng 2: Chuyển hình vẽ/đồ thị thành mã TikZ pure"""
    def process(self, file_bytes: bytes, mime_type: str, model: str, extra_prompt: str) -> str:
        prompt = "Hãy dựng lại hình vẽ/đồ thị/bảng biến thiên trong ảnh này thành mã TikZ hoặc tkz-tab."
        sys_prompt = PROMPTS["TIKZ_ONLY"]
        if extra_prompt.strip():
            sys_prompt += f"\nYêu cầu bổ sung: {extra_prompt.strip()}"

        contents = [
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            prompt
        ]
        return self.api_service.generate_with_fallback(contents, sys_prompt, model)


class ExTestSolverProcessor(BaseProcessor):
    """Chức năng 3: Chuyển bài toán thành ex_test + Tự giải nếu chưa có lời giải"""
    def process(self, file_bytes: bytes, mime_type: str, model: str, extra_prompt: str) -> str:
        prompt = "Nhận diện bài toán, viết theo dạng ex_test. Nếu chưa có lời giải, hãy tự giải chi tiết và thêm vào môi trường \\loigiai."
        sys_prompt = PROMPTS["EX_TEST_SOLVE"]
        if extra_prompt.strip():
            sys_prompt += f"\nYêu cầu bổ sung: {extra_prompt.strip()}"

        contents = [
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            prompt
        ]
        return self.api_service.generate_with_fallback(contents, sys_prompt, model)


class ProcessorFactory:
    """Factory Pattern để khởi tạo đúng Processor theo chế độ chọn từ UI"""
    @staticmethod
    def get_processor(mode: str, api_service: GeminiAPIService) -> BaseProcessor:
        if mode == "ex_test":
            return ExTestProcessor(api_service)
        elif mode == "tikz":
            return TikZProcessor(api_service)
        elif mode == "ex_test_solve":
            return ExTestSolverProcessor(api_service)
        else:
            raise ValueError(f"Chế độ không hợp lệ: {mode}")
