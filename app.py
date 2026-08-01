import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent
from streamlit_paste_button import paste_image_button

st.set_page_config(
    page_title="Math OCR Pro - Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# STYLING FIX SIZE & CHUẨN MÀU STUDIO MONOCHROME
FIXED_LAYOUT_CSS = CUSTOM_CSS + """
<style>
    :root {
        --primary-indigo: #4F46E5 !important;
        --primary-hover: #4338CA !important;
        --bg-editor: #181825 !important;
        --border-subtle: #313244 !important;
        --text-color: #CDD6F4 !important;
    }

    /* Triệt tiêu màu đỏ viền focus mặc định */
    div[data-baseweb="textarea"]:focus-within,
    div[data-baseweb="input"]:focus-within {
        border-color: var(--primary-indigo) !important;
        box-shadow: 0 0 0 1px var(--primary-indigo) !important;
    }

    /* 1. KHUNG EDITOR CHÍNH - FIX KÍCH THƯỚC CỐ ĐỊNH */
    .editor-container-box {
        background-color: var(--bg-editor);
        border: 1.5px solid var(--border-subtle);
        border-radius: 12px;
        padding: 14px;
        height: 220px !important; /* Cố định độ cao khung main */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
    }

    /* Tối ưu Upload Dropzone nằm lọt lòng bên trong Box Editor */
    div[data-testid="stFileUploader"] section {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px dashed var(--border-subtle) !important;
        border-radius: 8px !important;
        padding: 10px !important;
        height: 120px !important; /* Fix độ cao vùng kéo thả */
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stFileUploader"] section:hover {
        border-color: var(--primary-indigo) !important;
        background-color: rgba(79, 70, 229, 0.05) !important;
    }

    /* Căn chỉnh lại nút Clipboard góc trên */
    div[data-testid="stCustomComponentV1"] iframe {
        height: 38px !important;
        width: 100% !important;
    }

    /* 2. KHUNG PROMPT PHÍA DƯỚI - FIX KÍCH THƯỚC CỐ ĐỊNH */
    .stTextArea textarea {
        background-color: var(--bg-editor) !important;
        border: 1.5px solid var(--border-subtle) !important;
        border-radius: 10px !important;
        color: var(--text-color) !important;
        font-size: 13.5px !important;
        height: 80px !important; /* Cố định độ cao khung Prompt */
        resize: none !important;
    }

    /* 3. NÚT CONVERT Ở GÓC DƯỚI BÊN PHẢI */
    .stButton button[kind="primary"] {
        background-color: var(--primary-indigo) !important;
        border: none !important;
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: var(--primary-hover) !important;
        box-shadow: 0 4px 16px rgba(79, 70, 229, 0.4) !important;
    }
    .stButton button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--border-subtle) !important;
        color: #A6ADC8 !important;
        height: 42px !important;
        border-radius: 8px !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: var(--primary-indigo) !important;
        color: var(--primary-indigo) !important;
    }
</style>
"""
st.markdown(FIXED_LAYOUT_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def __init__(self):
        pass

    def run(self):
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

        # CỘT 1: THIẾT KẾ KHUNG CỐ ĐỊNH THEO WIREFRAME
        with col1:
            st.markdown("### 📥 Box Editor Đầu Vào")
            
            # --- BOX 1: EDITOR MAIN CONTAINER (FIXED SIZE) ---
            head_col, btn_col = st.columns([6, 4])
            with head_col:
                st.caption("Dán hoặc kéo thả ảnh/PDF vào đây:")
            with btn_col:
                # Nút Dán Clipboard nằm gọn bên trên góc phải
                paste_result = paste_image_button(
                    label="📋 Paste Clipboard",
                    background_color="#4F46E5",
                    text_color="#FFFFFF",
                    hover_background_color="#4338CA",
                )

            uploaded_files = st.file_uploader(
                "Upload Box", 
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )

            # Xử lý Paste
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

            # Xử lý Upload
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

            # Thanh hiển thị danh sách các tệp đã nhận
            if st.session_state.get("input_images"):
                cols = st.columns(min(len(st.session_state["input_images"]), 4))
                for idx, item in enumerate(st.session_state["input_images"]):
                    with cols[idx % 4]:
                        if item["mime"] == "application/pdf":
                            st.info(f"📄 {item['name'][:6]}..", icon=":material/description:")
                        elif item.get("preview"):
                            st.image(item["preview"], use_container_width=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- BOX 2: YÊU CẦU BỔ SUNG AI (FIXED SIZE 80PX) ---
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI", 
                value=st.session_state["extra_notes_val"],
                placeholder="Điền nội dung yêu cầu thêm AI vào box này...",
                label_visibility="collapsed"
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # --- DƯỚI CÙNG: NÚT ACTION CĂN PHẢI ---
            b_col1, b_col2, b_col3 = st.columns([4, 3, 3])
            with b_col2:
                btn_clear = st.button("🗑️ Xóa tệp", type="secondary", use_container_width=True)
            with b_col3:
                btn_process = st.button("Convert", type="primary", use_container_width=True)

            # Sự kiện thực thi
            if btn_clear:
                st.session_state["input_images"] = []
                if "last_pasted" in st.session_state:
                    del st.session_state["last_pasted"]
                st.rerun()

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not st.session_state.get("input_images"):
                    st.error("Chưa có ảnh/PDF nào trong Box Editor!", icon="🖼️")
                else:
                    with st.spinner("Đang trích xuất mã toán..."):
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
                            st.toast("Đã chuyển đổi xong!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}", icon="❌")

        # CỘT 2: OUTPUT LATEX CODE
        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
