import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import time

# -----------------------------------------------------------------------------
# Cấu hình Trang Web Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Math OCR - Chuyển ảnh sang LaTeX", page_icon="🧮", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .stCodeBlock { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# System Instruction chuẩn hóa cho Math OCR & LaTeX
# -----------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """
Bạn là một chuyên gia OCR Toán học nâng cao và biên soạn tài liệu LaTeX chuyên nghiệp.
Nhiệm vụ của bạn là nhận diện chính xác nội dung công thức toán học, bài toán, bảng biến thiên, hoặc đồ thị từ hình ảnh và chuyển đổi sang mã LaTeX chuẩn.

Quy tắc bắt buộc:
1. TRẢ VỀ MÃ LATEX THUẦN TÚY, KHÔNG kèm các câu dẫn dắt hay giải thích (như "Đây là mã LaTeX...").
2. Đảm bảo đúng các chuẩn ký hiệu toán học: phân số (\\frac), tích phân (\\int), căn thức (\\sqrt), giới hạn (\\lim), ma trận (matrix/pmatrix), các ký hiệu Hy Lạp, v.v.
3. Nếu ảnh là BẢNG BIẾN THIÊN hoặc ĐỒ THỊ, ưu tiên chuyển đổi thành mã gói `tkz-tab` hoặc môi trường `array`/`tikzpicture` chuẩn.
4. Nếu hình ảnh chứa bài toán nhiều dòng, sử dụng môi trường align*, gather*, hoặc split phù hợp.
5. Giữ nguyên cấu trúc logic của bài toán.
"""

def get_available_models(api_key: str):
    """Lấy danh sách các model thực tế hỗ trợ generateContent từ API Key của bạn"""
    try:
        client = genai.Client(api_key=api_key)
        models_list = []
        for m in client.models.list():
            name = m.name.replace("models/", "") if hasattr(m, 'name') else str(m)
            if "gemini" in name.lower():
                models_list.append(name)
        return models_list if models_list else ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    except Exception:
        return ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]

def convert_image(image_bytes: bytes, mime_type: str, api_key: str, model_name: str, extra_prompt: str) -> str:
    """Gọi Gemini API xử lý ảnh với cơ chế fallback tự động nếu dính lỗi 429 Quota"""
    client = genai.Client(api_key=api_key)
    prompt = "Hãy nhận diện và chuyển đổi chính xác toàn bộ biểu thức/nội dung toán học trong ảnh này thành mã LaTeX chuẩn."
    
    sys_prompt = SYSTEM_INSTRUCTION
    if extra_prompt.strip():
        sys_prompt += f"\nYêu cầu bổ sung từ người dùng: {extra_prompt.strip()}"

    # Danh sách ưu tiên chuyển đổi nếu mô hình được chọn chạm trần Rate Limit (429)
    fallback_models = [model_name, "gemini-1.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]
    fallback_models = list(dict.fromkeys(fallback_models)) # Bỏ trùng lặp

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
            return response.text
        except Exception as e:
            last_exception = e
            # Nếu dính lỗi 429 (Resource Exhausted), tạm nghỉ 2s rồi thử model tiếp theo
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                time.sleep(2)
                continue
            else:
                raise e

    raise last_exception

# -----------------------------------------------------------------------------
# Thanh bên (Sidebar)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Cấu hình App")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    
    # Tự động quét Model khả dụng
    available_models = []
    if api_key:
        available_models = get_available_models(api_key)
    else:
        available_models = ["Vui lòng nhập API Key trước"]
        
    model_choice = st.selectbox(
        "Mô hình Gemini khả dụng", 
        available_models,
        index=0,
        help="Danh sách mô hình được truy vấn trực tiếp từ tài khoản Google AI của bạn."
    )
    
    extra_notes = st.text_area(
        "Ghi chú bổ sung (Tùy chọn)", 
        placeholder="VD: Nếu là bảng biến thiên hãy dùng gói tkz-tab..."
    )

# -----------------------------------------------------------------------------
# Giao diện chính (Main UI)
# -----------------------------------------------------------------------------
st.title("🧮 Math Image to LaTeX Web App")
st.caption("Ứng dụng nhận diện và chuyển đổi công thức toán học từ ảnh sang mã LaTeX.")

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Tải ảnh bài toán / công thức")
    uploaded = st.file_uploader("Chọn ảnh PNG, JPG, WEBP", type=["png", "jpg", "jpeg", "webp"])
    if uploaded:
        st.image(uploaded, use_container_width=True)

with col2:
    st.subheader("2. Mã LaTeX & Xem trước")
    if uploaded and st.button("🚀 Chuyển đổi ngay", type="primary", use_container_width=True):
        if not api_key:
            st.error("Vui lòng nhập Gemini API Key ở thanh bên trái!")
        else:
            with st.spinner("Đang nhận diện..."):
                try:
                    res = convert_image(uploaded.getvalue(), uploaded.type, api_key, model_choice, extra_notes)
                    
                    # Làm sạch mã LaTeX trả về
                    clean_res = res.strip()
                    if clean_res.startswith("```latex"):
                        clean_res = clean_res[8:]
                    if clean_res.startswith("```"):
                        clean_res = clean_res[3:]
                    if clean_res.endswith("```"):
                        clean_res = clean_res[:-3]
                    clean_res = clean_res.strip()
                    
                    st.session_state["result"] = clean_res
                    st.success("Thành công!")
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if "result" in st.session_state and st.session_state["result"]:
        latex = st.session_state["result"]
        tab1, tab2 = st.tabs(["👁️ Xem trước (Render)", "💻 Mã LaTeX"])
        with tab1:
            if "\\begin{tkz" in latex or "\\begin{tikzpicture}" in latex:
                st.info("📌 Đoạn mã chứa môi trường TikZ/tkz-tab. Bạn hãy copy mã bên tab 'Mã LaTeX' để dán vào Overleaf/LaTeX Editor.")
            st.markdown(f"$${latex}$$")
        with tab2:
            st.code(latex, language="latex")
