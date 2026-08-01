# processors.py
import re
from abc import ABC, abstractmethod
from gemini_service import GeminiAPIService

class BaseProcessor(ABC):
    def __init__(self, api_service: GeminiAPIService):
        self.api_service = api_service

    def clean_latex_output(self, text: str) -> str:
        """Hàm lọc bỏ toàn bộ lời dẫn, markdown code blocks để lấy mã LaTeX thuần"""
        if not text:
            return ""
        
        # 1. Bỏ khối ```latex ... ``` hoặc ``` ... ```
        text = re.sub(r'```(?:latex|tex)?\n?', '', text)
        text = re.sub(r'```$', '', text)
        
        # 2. Bỏ các dòng lời dẫn tiếng Việt / tiếng Anh thường gặp ở đầu
        # Tìm vị trí bắt đầu thực sự của mã LaTeX (\begin, %, \document, \tikz, \ex...)
        first_code_match = re.search(r'(\\begin|%|\\documentclass|\\def|\\pgf|\\tikz|\\ex)', text)
        if first_code_match:
            text = text[first_code_match.start():]
            
        return text.strip()

    @abstractmethod
    def process(self, image_input, model_name: str, system_instruction: str, extra_notes: str) -> str:
        pass


class ExTestProcessor(BaseProcessor):
    def process(self, image_input, model_name: str, system_instruction: str, extra_notes: str) -> str:
        prompt = system_instruction
        if extra_notes:
            prompt += f"\n\nYêu cầu bổ sung:\n{extra_notes}"
            
        raw_result = self.api_service.generate_content(model_name, prompt, image_input)
        return self.clean_latex_output(raw_result)


class ExTestSolveProcessor(BaseProcessor):
    def process(self, image_input, model_name: str, system_instruction: str, extra_notes: str) -> str:
        prompt = system_instruction
        if extra_notes:
            prompt += f"\n\nYêu cầu bổ sung:\n{extra_notes}"
            
        raw_result = self.api_service.generate_content(model_name, prompt, image_input)
        return self.clean_latex_output(raw_result)


class TikZProcessor(BaseProcessor):
    def process(self, image_input, model_name: str, system_instruction: str, extra_notes: str) -> str:
        prompt = system_instruction
        if extra_notes:
            prompt += f"\n\nYêu cầu bổ sung:\n{extra_notes}"
            
        raw_result = self.api_service.generate_content(model_name, prompt, image_input)
        return self.clean_latex_output(raw_result)


class ProcessorFactory:
    @staticmethod
    def get_processor(mode: str, api_service: GeminiAPIService) -> BaseProcessor:
        processors = {
            "ex_test": ExTestProcessor,
            "ex_test_solve": ExTestSolveProcessor,
            "tikz": TikZProcessor
        }
        processor_cls = processors.get(mode)
        if not processor_cls:
            raise ValueError(f"Chức năng '{mode}' không hợp lệ.")
        return processor_cls(api_service)
