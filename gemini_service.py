import time
from google import genai
from google.genai import types
from config import SYSTEM_INSTRUCTION, NON_VISION_KEYWORDS, DEFAULT_MODELS

def is_vision_model(model_name: str) -> bool:
    """Kiểm tra model hỗ trợ Vision/Multimodal dựa trên tên"""
    name_lower = model_name.lower()
    for keyword in NON_VISION_KEYWORDS:
        if keyword in name_lower:
            return False
    return "gemini" in name_lower

def get_available_models(api_key: str) -> list[str]:
    """Quét và trả về danh sách các Vision Models khả dụng từ API Key"""
    try:
        client = genai.Client(api_key=api_key)
        valid_models = []
        for m in client.models.list():
            name = m.name.replace("models/", "") if hasattr(m, 'name') else str(m)
            if is_vision_model(name):
                valid_models.append(name)
        
        valid_models.sort(key=lambda x: ("lite" in x, "pro" in x, "preview" in x))
        return valid_models if valid_models else DEFAULT_MODELS
    except Exception:
        return DEFAULT_MODELS

def convert_image_to_latex(
    image_bytes: bytes, 
    mime_type: str, 
    api_key: str, 
    selected_model: str, 
    extra_prompt: str
) -> str:
    """Xử lý gọi API Gemini với cơ chế tự động Fallback và Retry khi gặp lỗi Quota/404/400"""
    client = genai.Client(api_key=api_key)
    prompt = "Hãy nhận diện và chuyển đổi chính xác toàn bộ biểu thức/nội dung toán học trong ảnh này thành mã LaTeX chuẩn."
    
    sys_prompt = SYSTEM_INSTRUCTION
    if extra_prompt.strip():
        sys_prompt += f"\nYêu cầu bổ sung từ người dùng: {extra_prompt.strip()}"

    available_list = get_available_models(api_key)
    fallback_models = [selected_model] + [m for m in available_list if m != selected_model]

    last_exception = None

    for m in fallback_models:
        try:
            response = client.models.generate_content(
                model=m,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    system_instruction=sys_prompt,
                    temperature=0.1
                )
            )
            return _clean_latex_output(response.text)
        except Exception as e:
            last_exception = e
            err_str = str(e)
            if "400" in err_str or "INVALID_ARGUMENT" in err_str or "404" in err_str or "NOT_FOUND" in err_str:
                continue
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                time.sleep(2)
                continue
            raise e

    raise last_exception

def _clean_latex_output(text: str) -> str:
    """Làm sạch markdown code blocks trả về từ model"""
    clean_res = text.strip()
    if clean_res.startswith("```latex"):
        clean_res = clean_res[8:]
    if clean_res.startswith("```"):
        clean_res = clean_res[3:]
    if clean_res.endswith("```"):
        clean_res = clean_res[:-3]
    return clean_res.strip()
