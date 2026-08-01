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
        # Bóc tách mã nằm trong block ```latex ... ``` hoặc ```xml ... ```
        match = re.search(r"```(?:latex|tikz|tex)?\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return text.strip()

class LaTeXProcessor(BaseProcessor):
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "", **kwargs) -> str:
        """Xử lý xuất tài liệu LaTeX tiêu chuẩn có đầy đủ preamble và môi trường document"""
        system_instruction = PROMPTS.get("STANDARD_LATEX", (
            "Bạn là một chuyên gia biên soạn tài liệu LaTeX toán học.\n"
            "Chuyển đổi đầu vào thành file LaTeX hoàn chỉnh với đầy đủ \\documentclass, các gói lệnh và \\begin{document}.\n"
            "Chỉ trả về duy nhất đoạn mã LaTeX trong khối ```latex ... ```."
        ))

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
    def process(self, input_data: List[Dict[str, Any]], model: str, extra_prompt: str = "", add_solution: bool = True, **kwargs) -> str:
        """
        Xử lý bài toán theo chuẩn gói ex_test / LaTeX toán học.
        Support 3 dạng câu hỏi (Trắc nghiệm, Đúng/Sai, Trả lời ngắn), tự động xóa bảng đáp án, 
        và bổ sung tùy chọn sinh lời giải chi tiết hay giữ nguyên gốc.
        `input_data` nhận danh sách các dict: [{"bytes": b"...", "mime": "image/png"}, ...]
        """
        # Chọn prompt phù hợp với tùy chọn Lời giải
        if add_solution:
            system_instruction = PROMPTS.get("EX_TEST_SOLVE", PROMPTS.get("EX_TEST", ""))
        else:
            system_instruction = PROMPTS.get("EX_TEST", "")

        # Bổ sung các chỉ thị bắt buộc về cấu trúc & bỏ bảng
        requirements_instruction = (
            "\n\nQUY TẮC BẮT BUỘC:"
            "\n1. Tự động phân loại chính xác 3 dạng câu hỏi:"
            "\n   - Trắc nghiệm 4 lựa chọn: \\choice{A}{B}{C}{D}"
            "\n   - Trắc nghiệm Đúng/Sai: \\choiceTF{\\True A}{B}{\\True C}{D}"
            "\n   - Trắc nghiệm trả lời ngắn: \\shortans{Đáp số}"
            "\n2. BỎ HOÀN TOÀN các bảng tô/điền đáp án (tabular, table) trong đề gốc."
        )

        full_prompt = system_instruction + requirements_instruction
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
        """Xử lý dựng hình vẽ bằng TikZ / tkz-euclide / tkz-tab"""
        system_instruction = PROMPTS.get("TIKZ_ONLY", (
            "Bạn là chuyên gia dựng hình học toán học bằng TikZ và tkz-euclide trong LaTeX.\n"
            "Hãy chuyển hình ảnh hoặc mô tả bài toán thành mã TikZ hoàn chỉnh, tối ưu và đẹp mắt.\n"
            "Chỉ trả về mã trong khối ```latex ... ```."
        ))

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
        elif "latex" in mode_lower and "ex_test" not in mode_lower:
            return LaTeXProcessor(api_service)
        else:
            # Mặc định dùng ExTestProcessor cho đề thi/bài toán
            return ExTestProcessor(api_service)
