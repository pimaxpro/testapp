import streamlit as st
from google import genai
from google.genai import types
from PIL import Image
import io
import time

# -----------------------------------------------------------------------------
# Cấu hình Trang Web & Custom CSS Trang trí Siêu Đẹp
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Math OCR Pro - Image to LaTeX", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS tùy chỉnh theo phong cách Modern Dark/Light Sleek
st.markdown("""
    <style>
    /* Bố cục chung */
    .main .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 2rem;
        max-width: 95%;
    }
    
    /* Style Card Container cho 2 Cột */
    .css-card {
        background-color: var(--background-secondary-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    
    /* Header & Badge Styling */
    .header-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    /* Nút bấm chuyển đổi chính */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
        background: linear-gradient(90deg, #4F46E5, #3B82F6);
        border: none;
        color: white;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }

    /* Style khung hiển thị Code */
    .stCodeBlock {
        border-radius: 10px !important;
        border: 1px solid rgba(79, 70, 229, 0.2) !important;
    }
    
    /* Ẩn bớt footer mặc định */
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# System Instruction cho Math OCR & LaTeX
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

def is_vision_model(model_name: str) -> bool:
    """Kiểm tra model hỗ trợ Vision/Multimodal"""
    name_lower = model_name.lower()
    non_vision_keywords = ["tts", "audio", "embed", "text-only", "imagen"]
    for keyword in non_vision_keywords:
        if keyword in name_lower:
            return False
    return "gemini" in name_lower

def get_available_models(api_key: str):
    """Lấy danh sách các Vision models thực sự hỗ trợ xử lý ảnh từ API Key"""
    try:
        client = genai.Client(api_key=api_key)
        valid_models = []
        for m in client.models.list():
            name = m.name.replace("models/", "") if hasattr(m, 'name') else str(m)
            if is_vision_model(name):
                valid_models.append(name)
        valid_models.sort(key=lambda x: ("lite" in x, "pro" in x, "preview" in x))
        return valid_models if valid_models else ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    except Exception:
        return ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

def convert_image(image_bytes: bytes, mime_type: str, api_key: str, selected_model: str, extra_prompt: str) -> str:
    """Xử lý API với fallback tự động"""
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
            return response.text
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

# -----------------------------------------------------------------------------
# Thanh bên (Sidebar)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ **Cấu hình Hệ thống**")
    st.markdown("---")
    
    api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
    
    available_models = []
    if api_key:
        available_models = get_available_models(api_key)
    else:
        available_models = ["Vui lòng nhập API Key trước"]
        
    model_choice = st.selectbox(
        "Mô hình Gemini Vision", 
        available_models,
        index=0,
        help="Danh sách mô hình đọc ảnh khả dụng trên tài khoản của bạn."
    )
    
    st.markdown("---")
    extra_notes = st.text_area(
        "📝 **Ghi chú/Yêu cầu bổ sung**", 
        placeholder="VD: Dùng tkz-tab cho BBT, dùng align* cho hệ phương trình...",
        height=120
    )
    
    st.caption("✨ Tự động tối ưu mã cho Overleaf, LaTeX Studio và các trình biên soạn chuyên nghiệp.")

# -----------------------------------------------------------------------------
# Giao diện chính (Main UI)
# -----------------------------------------------------------------------------
# Header
st.markdown("<h1 class='header-title'>🧮 Math OCR Studio Pro</h1>", unsafe_allow_html=True)
st.markdown("Chuyển đổi hình ảnh bài toán, công thức, đồ thị & bảng biến thiên thành **mã LaTeX chuẩn**.")
st.write("")

# Chia 2 cột tỷ lệ 5:7 cho bố cục cân đối hơn
col1, col2 = st.columns([5, 7], gap="large")

# -----------------------------------------------------------------------------
# CỘT 1: INPUT (Hình ảnh & Điều khiển)
# -----------------------------------------------------------------------------
with col1:
    st.markdown("### 📸 **1. Tải ảnh đầu vào**")
    
    uploaded = st.file_uploader(
        "Thả ảnh hoặc bấm để chọn (PNG, JPG, WEBP)", 
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed"
    )
    
    if uploaded:
        # Container xem trước ảnh
        st.image(uploaded, use_container_width=True)
        
        # Nút chuyển đổi lớn
        convert_btn = st.button("🚀 Trích xuất Mã LaTeX", type="primary", use_container_width=True)
        if convert_btn:
            if not api_key:
                st.error("⚠️ Vui lòng nhập API Key ở thanh bên trái!")
            else:
                with st.spinner("⚡ Đang phân tích cấu trúc toán học..."):
                    try:
                        res = convert_image(uploaded.getvalue(), uploaded.type, api_key, model_choice, extra_notes)
                        
                        # Làm sạch mã
                        clean_res = res.strip()
                        if clean_res.startswith("```latex"):
                            clean_res = clean_res[8:]
                        if clean_res.startswith("```"):
                            clean_res = clean_res[3:]
                        if clean_res.endswith("```"):
                            clean_res = clean_res[:-3]
                        clean_res = clean_res.strip()
                        
                        st.session_state["result"] = clean_res
                        st.session_state["has_run"] = True
                        st.toast("Chuyển đổi thành công!", icon="✅")
                    except Exception as e:
                        st.error(f"❌ Lỗi: {e}")
    else:
        # Placeholder gợi ý khi chưa chọn ảnh
        st.info("👆 Hãy tải lên một bức ảnh chứa công thức toán hoặc đề bài để bắt đầu.")

# -----------------------------------------------------------------------------
# CỘT 2: OUTPUT (Kết quả Mã LaTeX Pure)
# -----------------------------------------------------------------------------
with col2:
    st.markdown("### 📄 **2. Kết quả Mã LaTeX**")
    
    if "result" in st.session_state and st.session_state["result"]:
        latex_code = st.session_state["result"]
        
        # Nhãn thông báo loại mã
        if "\\begin{tkz" in latex_code or "\\begin{tikzpicture}" in latex_code:
            st.warning("⚡ **Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)**")
        
        # Khung chứa code với nút Copy tích hợp sẵn của Streamlit
        st.code(latex_code, language="latex")
        
        # Ô Text area nhanh nếu người dùng muốn chỉnh sửa trực tiếp tại chỗ
        st.markdown("**Chỉnh sửa nhanh mã:**")
        edited_code = st.text_area(
            "Chỉnh sửa mã", 
            value=latex_code, 
            height=280, 
            label_visibility="collapsed"
        )
        
    else:
        # Giao diện chờ đẹp mắt
        st.markdown(
            """
            <div style="
                border: 2px dashed rgba(128, 128, 128, 0.3); 
                border-radius: 12px; 
                padding: 60px 20px; 
                text-align: center;
                color: #888888;
                margin-top: 10px;">
                <p style="font-size: 40px; margin-bottom: 10px;">💻</p>
                <p style="font-weight: 500;">Mã LaTeX sẽ xuất hiện ở đây sau khi bạn bấm "Trích xuất Mã LaTeX".</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
