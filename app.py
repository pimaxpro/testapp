import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io

st.set_page_config(page_title="Math OCR - Chuyển ảnh sang LaTeX", page_icon="🧮", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .stCodeBlock { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

SYSTEM_INSTRUCTION = """
Bạn là một chuyên gia OCR Toán học nâng cao và biên soạn tài liệu LaTeX chuyên nghiệp.
Nhiệm vụ của bạn là nhận diện chính xác nội dung công thức toán học, bài toán, hoặc cấu trúc hình học/bảng biểu từ hình ảnh và chuyển đổi sang mã LaTeX chuẩn.

Quy tắc bắt buộc:
1. TRẢ VỀ MÃ LATEX THUẦN TÚY, KHÔNG kèm các câu dẫn dắt hay giải thích (như "Đây là mã LaTeX...").
2. Đảm bảo đúng các chuẩn ký hiệu toán học: phân số (\\frac), tích phân (\\int), căn thức (\\sqrt), giới hạn (\\lim), ma trận (matrix/pmatrix), các ký hiệu Hy Lạp, v.v.
3. Nếu hình ảnh chứa bài toán nhiều dòng, sử dụng môi trường align*, gather*, hoặc split phù hợp.
4. Giữ nguyên cấu trúc logic của bài toán.
"""

def convert_image(image_bytes: bytes, mime_type: str, api_key: str, model_name: str, extra_prompt: str) -> str:
    client = genai.Client(api_key=api_key)
    prompt = "Hãy nhận diện và chuyển đổi chính xác toàn bộ biểu thức/nội dung toán học trong ảnh này thành mã LaTeX chuẩn."
    
    sys_prompt = SYSTEM_INSTRUCTION
    if extra_prompt.strip():
        sys_prompt += f"\nYêu cầu bổ sung: {extra_prompt.strip()}"

    response = client.models.generate_content(
        model=model_name,
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

# Sidebar
with st.sidebar:
    st.title("⚙️ Cấu hình App")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    model_choice = st.selectbox("Mô hình", ["gemini-2.5-flash", "gemini-2.5-pro"])
    extra_notes = st.text_area("Ghi chú bổ sung (Tùy chọn)", placeholder="VD: Nếu là bảng biến thiên hãy dùng tkz-tab...")

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
                    clean_res = res.replace("```latex", "").replace("```", "").strip()
                    st.session_state["result"] = clean_res
                except Exception as e:
                    st.error(f"Lỗi: {e}")

    if "result" in st.session_state:
        latex = st.session_state["result"]
        tab1, tab2 = st.tabs(["👁️ Xem trước (Render)", "💻 Mã LaTeX"])
        with tab1:
            st.markdown(f"$${latex}$$")
        with tab2:
            st.code(latex, language="latex")
