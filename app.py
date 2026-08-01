import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent
from streamlit_paste_button import paste_image_button

st.set_page_config(
    page_title="Math OCR Pro - OOP Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# THIẾT KẾ ĐỒNG BỘ GIAO DIỆN MONOCHROME / SINGLE-TONE CHUYÊN NGHIỆP
STUDIO_THEME_CSS = CUSTOM_CSS + """
<style>
    /* 1. ĐỒNG BỘ BẢNG MÀU CHỦ ĐẠO (SINGLE TONE) */
    :root {
        --primary-color: #4F46E5 !important;
        --primary-hover: #4338CA !important;
        --accent-glow: rgba(79, 70, 229, 0.25) !important;
        --bg-card: #181825 !important;
        --border-color: #313244 !important;
        --text-muted: #A6ADC8 !important;
    }

    /* TRIỆT TIÊU TOÀN BỘ MÀU ĐỎ / ĐỔI VIỀN MẶC ĐỊNH CỦA STREAMLIT */
    div[data-baseweb="input"]:focus-within, 
    div[data-baseweb="textarea"]:focus-within {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 1px #4F46E5 !important;
    }
    
    /* 2. CHUẨN HÓA KÍCH THƯỚC & CĂN GIỮA ICON NÚT PASTE CLIPBOARD */
    div[data-testid="stCustomComponentV1"] iframe {
        height: 48px !important;
        width: 100% !important;
    }

    /* 3. THIẾT KẾ NÚT FILE UPLOADER CÂN BẰNG 100% VỚI NÚT PASTE */
    div[data-testid="stFileUploader"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0 16px !important;
        background-color: #4F46E5 !important;
        border: 1px solid #4F46E5 !important;
        border-radius: 8px !important;
        height: 48px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFileUploader"] section:hover {
        background-color: #4338CA !important;
        border-color: #4338CA !important;
        box-shadow: 0 4px 12px var(--accent-glow) !important;
    }
    div[data-testid="stFileUploader"] section * {
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    /* Hide non-essential drag & drop label to match button layout */
    div[data-testid="stFileUploader"] section small,
    div[data-testid="stFileUploader"] section span[data-testid="stIconMaterial"] {
        display: none !important;
    }
    div[data-testid="stFileUploader"] section div {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    div[data-testid="stFileUploader"] section div::before {
        content: "📁";
        font-size: 16px;
    }

    /* 4. ĐỒNG BỘ KHUNG THẺ PREVIEW VÀ TEXTAREA */
    .stTextArea textarea {
        background-color: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        color: #CDD6F4 !important;
    }
    .stTextArea textarea:focus {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 1px #4F46E5 !important;
    }

    /* 5. CĂN CHỈNH NÚT THỰC THI (EQUAL HEIGHT & ALIGNMENT) */
    .stButton button {
        height: 44px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton button[kind="primary"] {
        background-color: #4F46E5 !important;
        border: 1px solid #4F46E5 !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #4338CA !important;
        box-shadow: 0 4px 12px var(--accent-glow) !important;
    }
    .stButton button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        color: #CDD6F4 !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: #4F46E5 !important;
        color: #4F46E5 !important;
    }
</style>
"""
st.markdown(STUDIO_THEME_CSS, unsafe_allow_html=True)

class MathOCRApp:
    """Controller chính điều phối toàn bộ ứng dụng"""
    def __init__(self):
        pass

    def run(self):
        # KHỞI TẠO SESSION STATE
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        # SIDEBAR
        api_key, mode, selected_model = UIComponent.render_sidebar(api_service)
        
        api_service.api_key = api_key
        if api_key and not getattr(api_service, 'client', None):
            api_service.client = GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # CỘT 1: INPUT COMPONENT
        with col1:
            st.markdown("### 📥 Dữ liệu đầu vào")
            
            # 2 NÚT NGUỒN VÀO ĐẶT SONG SONG VỚI CÙNG TỶ LỆ KÍCH THƯỚC
            in_col1, in_col2 = st.columns(2, gap="small")

            with in_col1:
                paste_result = paste_image_button(
                    label="📋 Dán từ Clipboard",
                    background_color="#4F46E5",
                    text_color="#FFFFFF",
                    hover_background_color="#4338CA",
                )

            with in_col2:
                uploaded_files = st.file_uploader(
                    "Tải tệp từ máy", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed"
                )

            # Xử lý dán Clipboard
            if paste_result.image_data is not None:
                image = paste_result.image_data
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_bytes = buf.getvalue()
                
                if "last_pasted" not in st.session_state or st.session_state["last_pasted"] != img_bytes:
                    st.session_state["last_pasted"] = img_bytes
                    st.session_state["input_images"].append({
                        "name": f"Clipboard_{len(st.session_state['input_images']) + 1}.png",
                        "bytes": img_bytes,
                        "mime": "image/png",
                        "preview": image
                    })
                    st.toast("Đã dán ảnh!", icon="📋")

            # Xử lý chọn tệp từ máy
            if uploaded_files:
                for file in uploaded_files:
                    file_bytes = file.getvalue()
                    mime_type = file.type
                    
                    if not any(item.get("name") == file.name for item in st.session_state["input_images"]):
                        preview_img = Image.open(io.BytesIO(file_bytes)) if mime_type != "application/pdf" else None
                        st.session_state["input_images"].append({
                            "name": file.name,
                            "bytes": file_bytes,
                            "mime": mime_type,
                            "preview": preview_img
                        })

            # KHU VỰC PREVIEW DANH SÁCH FILE ĐÃ NHẬN
            if st.session_state.get("input_images"):
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                st.caption(f"Đã tải lên **{len(st.session_state['input_images'])}** tệp:")
                cols = st.columns(min(len(st.session_state["input_images"]), 4))
                for idx, item in enumerate(st.session_state["input_images"]):
                    with cols[idx % 4]:
                        if item["mime"] == "application/pdf":
                            st.info(f"📄 {item['name'][:10]}...", icon=":material/description:")
                        elif item.get("preview"):
                            st.image(item["preview"], use_container_width=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # PROMPT YÊU CẦU BỔ SUNG
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "💡 Yêu cầu bổ sung cho AI", 
                value=st.session_state["extra_notes_val"],
                height=110,
                placeholder="Ví dụ: Chỉ xuất mã TikZ, dùng gói ex_test..."
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

            # NÚT THỰC THI CHÍNH VA NÚT XÓA
            btn_col1, btn_col2 = st.columns([7, 3], gap="small")
            with btn_col1:
                btn_process = st.button(
                    "🚀 Trích xuất & Chuyển đổi", 
                    type="primary", 
                    use_container_width=True
                )
            with btn_col2:
                btn_clear = st.button(
                    "🗑️ Xóa hết", 
                    type="secondary", 
                    use_container_width=True
                )

            # SỰ KIỆN XỬ LÝ
            if btn_clear:
                st.session_state["input_images"] = []
                if "last_pasted" in st.session_state:
                    del st.session_state["last_pasted"]
                st.rerun()

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên trái!", icon="🔑")
                elif not st.session_state.get("input_images"):
                    st.error("Chưa chọn ảnh/PDF nào!", icon="🖼️")
                else:
                    with st.spinner("Đang xử lý mã toán..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            input_list = st.session_state["input_images"]
                            
                            try:
                                result_code = processor.process(
                                    input_data=input_list,
                                    model=selected_model,
                                    extra_prompt=extra_prompt
                                )
                            except TypeError:
                                first_item = input_list[0]
                                result_code = processor.process(
                                    file_bytes=first_item["bytes"],
                                    mime_type=first_item["mime"],
                                    model=selected_model,
                                    extra_prompt=extra_prompt
                                )

                            st.session_state["result"] = result_code
                            st.toast("Trích xuất thành công!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi xử lý: {e}", icon="❌")

        # CỘT 2: OUTPUT LATEX CODE NGUYÊN BẢN
        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
