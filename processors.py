# processors.py
import re
from typing import List, Dict, Any, Optional
from config import PROMPTS

class BaseProcessor:
    def __init__(self, api_service):
        self.api_service = api_service

    def clean_latex(self, text: str) -> str:
        """Làm sạch đầu ra, lấy phần nội dung mã LaTeX/TikZ"""
        if not text:
            return ""
        match = re.search(r"```(?:latex|tikz|tex)?\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()

class LaTeXProcessor(BaseProcessor):
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "", **kwargs) -> str:
        """Chức năng 1: Chuyển file sang LaTeX đầy đủ cấu trúc document"""
        system_instruction = PROMPTS.get("STANDARD_LATEX", "")

        full_prompt = system_instruction
        if extra_prompt.strip():
            full_prompt += f"\n\nYêu cầu bổ sung từ người dùng:\n{extra_prompt}"

        raw_response = self.api_service.generate_content(
            input_data=input_data,
            prompt=full_prompt,
            model=model
        )
        return self.clean_latex(raw_response)

class ExTestProcessor(BaseProcessor):
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "", add_solution: bool = False, **kwargs) -> str:
        """Chức năng 2: Chuyển bài toán sang ex_test (Tùy chọn Giữ nguyên gốc / Thêm lời giải)"""
        if add_solution:
            system_instruction = PROMPTS.get("EX_TEST_SOLVE", "")
        else:
            system_instruction = PROMPTS.get("EX_TEST", "")

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
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "", **kwargs) -> str:
        """Chức năng 3: Chuyển ảnh sang TikZ / tkz-tab"""
        system_instruction = PROMPTS.get("TIKZ_ONLY", "")

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
        if "Latex" in mode or "1." in mode:
            return LaTeXProcessor(api_service)
        elif "tikz" in mode.lower() or "3." in mode:
            return TikZProcessor(api_service)
        else:
            return ExTestProcessor(api_service)
