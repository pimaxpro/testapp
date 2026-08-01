import re
from typing import List, Dict, Any, Optional

class BaseProcessor:
    def __init__(self, api_service):
        self.api_service = api_service

    def clean_latex(self, text: str) -> str:
        """Làm sạch đầu ra, lấy phần nội dung mã LaTeX/TikZ"""
        if not text:
            return ""
        # Bóc tách mã nằm trong block ```latex ... ``` hoặc ```xml ... ```
        match = re.search(r"```(?:latex|tikz|tex)?\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()

class ExTestProcessor(BaseProcessor):
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "") -> str:
        """
        Xử lý bài toán theo chuẩn gói ex_test / LaTeX toán học.
        `input_data` nhận danh sách các dict: [{"bytes": b"...", "mime": "image/png"}, ...]
        """
        system_instruction = (
            "Bạn là một chuyên gia soạn thảo đề thi Toán bằng LaTeX chuẩn gói ex_test.\n"
            "Nhiệm vụ của bạn là chuyển đổi hình ảnh hoặc văn bản đề toán thành mã LaTeX chuẩn xác.\n"
            "Chỉ trả về duy nhất đoạn mã LaTeX trong khối ```latex ... ```, không giải thích gì thêm."
        )
        
        full_prompt = system_instruction
        if extra_prompt.strip():
            full_prompt += f"\n\nYêu cầu bổ sung từ người dùng:\n{extra_prompt}"

        raw_response = self.api_service.generate_content(
            input_data=input_data,
            prompt=full_prompt,
            model=model
        )
        return self.clean_latex(raw_response)

class TikZProcessor(BaseProcessor):
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "") -> str:
        """Xử lý dựng hình vẽ bằng TikZ / tkz-euclide"""
        system_instruction = (
            "Bạn là chuyên gia dựng hình học toán học bằng TikZ và tkz-euclide trong LaTeX.\n"
            "Hãy chuyển hình ảnh hoặc mô tả bài toán thành mã TikZ hoàn chỉnh, tối ưu và đẹp mắt.\n"
            "Chỉ trả về mã trong khối ```latex ... ```."
        )

        full_prompt = system_instruction
        if extra_prompt.strip():
            full_prompt += f"\n\nYêu cầu bổ sung:\n{extra_prompt}"

        raw_response = self.api_service.generate_content(
            input_data=input_data,
            prompt=full_prompt,
            model=model
        )
        return self.clean_latex(raw_response)

class ProcessorFactory:
    @staticmethod
    def get_processor(mode: str, api_service) -> BaseProcessor:
        mode_lower = mode.lower()
        if "tikz" in mode_lower:
            return TikZProcessor(api_service)
        else:
            # Mặc định dùng ExTestProcessor cho đề thi/bài toán
            return ExTestProcessor(api_service)
