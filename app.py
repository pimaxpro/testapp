import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent

# Loại bỏ hoàn toàn thư viện paste_image_button bên thứ 3

st.set_page_config(
    page_title="Math OCR Pro - Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# STYLING CSS CỐ ĐỊNH LAYOUT THEO ĐÚNG BẢN VẼ WIREFRAME
WIREFRAME_LAYOUT_CSS = CUSTOM_CSS + """
<style>
    /* 1. KHUNG BOX EDITOR (Container) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #D1D5DB !important;
        border-radius: 8px !important;
        padding: 4px !important;
        position: relative !important; /* Để neo nút Upload */
        margin-bottom: 20px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }

    /* 2. TEXT AREA NỀN TRONG SUỐT BÊN TRONG BOX */
    .stTextArea textarea {
        background-color: transparent !important;
        border: none !important;
        color: #111827 !important;
        font-size: 16px !important;
        padding: 16px !important;
        resize: none !important;
        box-shadow: none !important;
    }
    .stTextArea textarea:focus {
        box-shadow: none !important;
        border: none !important;
    }
    .stTextArea textarea::placeholder {
        color: #9CA3AF !important;
        font-weight: 400 !important;
    }
    
    /* 3. NÚT UPLOAD TREO GÓC TRÊN BÊN PHẢI CỦA BOX 1 */
    div[data-testid="stFileUploader"] {
        position: absolute !important;
        top: 12px !important;
        right: 12px !important;
        width: 100px !important;
        z-index: 10 !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
        height: 38px !important;
        border-radius: 6px !important;
        background-color: #BDBDBD !important; /* Màu xám theo thiết kế */
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stFileUploader"] section:hover {
        background-color: #A3A3A3 !important;
    }
    /* Ẩn icon mặc định và chèn chữ Upload */
    div[data-testid="stFileUploader"] section > div {
        display: none !important;
    }
    div[data-testid="stFileUploader"] section::after {
        content: "Upload";
        color: white;
        font-weight: 500;
        font-size: 15px;
    }
    /* Ẩn danh sách file mặc định của Streamlit */
    div[data-testid="stFileUploader"] ul {
        display: none !important;
    }

    /* 4. NÚT CONVERT XANH LAM BÊN DƯỚI */
    .stButton button[kind="primary"] {
        background-color: #45B6FE !important; /* Màu xanh lơ theo thiết kế */
        color: white !important;
        border: none !important;
        height: 44px !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        font-size: 16px !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #3AA0E0 !important;
    }
    
    /* Nút Xóa tệp phụ */
    .stButton button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #D1D5DB !important;
        color: #6B7280 !important;
        height: 44px !important;
        border-radius: 6px !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: #EF4444 !important;
        color: #EF4444 !important;
    }
</style>
"""
st.markdown(WIREFRAME_LAYOUT_CSS, unsafe_allow_html=True)

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

        # CỘT 1: THIẾT KẾ EXACTLY THEO WIREFRAME
        with col1:
            
            # --- BOX 1: EDITOR KÈM NÚT UPLOAD ---
            with st.container(border=True):
                # Khai báo File Uploader (CSS sẽ tự động kéo nó lên góc phải)
                uploaded_files = st.file_uploader(
                    "Upload Box", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed"
                )
                
                # Text Area cho phép gõ nội dung bài toán
                main_text = st.text_area(
                    "Box 1", 
                    height=200, 
                    placeholder="Đây là box editor, tự paste được ảnh vào đây, bỏ nút copy từ clipboard đi.", 
                    label_visibility="collapsed"
                )

                # Xử lý Logic File (Click vào nút Upload rồi bấm Ctrl+V vẫn nhận ảnh bình thường)
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

                # Hiển thị ảnh đã nạp ngay bên trong Box 1
                if st.session_state.get("input_images"):
                    st.markdown("<hr style='margin: 8px 0; border-color: #F3F4F6;'>", unsafe_allow_html=True)
                    cols = st.columns(5)
                    for idx, item in enumerate(st.session_state["input_images"]):
                        with cols[idx % 5]:
                            if item["mime"] == "application/pdf":
                                st.info("📄 PDF")
                            elif item.get("preview"):
                                st.image(item["preview"], use_container_width=True)

            # --- BOX 2: GHI CHÚ BỔ SUNG ---
            with st.container(border=True):
                if "extra_notes_val" not in st.session_state:
                    st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

                extra_prompt = st.text_area(
                    "Box 2", 
                    value=st.session_state["extra_notes_val"],
                    height=100,
                    placeholder="Điền nội dung yêu cầu thêm AI vào box này, thiết kế thêm cho tôi...",
                    label_visibility="collapsed"
                )
                st.session_state["extra_notes_val"] = extra_prompt

            # --- HÀNG NÚT BẤM DƯỚI CÙNG ---
            b_col1, b_col2, b_col3 = st.columns([5, 2, 3])
            with b_col2:
                btn_clear = st.button("Xóa tệp", type="secondary", use_container_width=True)
            with b_col3:
                btn_process = st.button("Convert", type="primary", use_container_width=True)

            # SỰ KIỆN XỬ LÝ
            if btn_clear:
                st.session_state["input_images"] = []
                st.rerun()

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not st.session_state.get("input_images") and not main_text.strip():
                    st.error("Vui lòng điền nội dung hoặc thêm ảnh!", icon="⚠️")
                else:
                    with st.spinner("Đang chuyển đổi toán học..."):
                        try:
                            # Ghép cả nội dung Box 1 và Box 2 để gửi cho AI
                            combined_prompt = ""
                            if main_text.strip():
                                combined_prompt += f"Nội dung văn bản kèm theo:\n{main_text}\n\n"
                            if extra_prompt.strip():
                                combined_prompt += f"Yêu cầu bổ sung:\n{extra_prompt}"

                            processor = ProcessorFactory.get_processor(mode, api_service)
                            input_list = st.session_state.get("input_images", [])
                            
                            try:
                                result_code = processor.process(
                                    input_data=input_list,
                                    model=selected_model,
                                    extra_prompt=combined_prompt
                                )
                            except TypeError:
                                # Fallback nếu process chỉ nhận 1 file
                                first_item = input_list[0] if input_list else {"bytes": None, "mime": None}
                                result_code = processor.process(
                                    file_bytes=first_item.get("bytes"),
                                    mime_type=first_item.get("mime"),
                                    model=selected_model,
                                    extra_prompt=combined_prompt
                                )

                            st.session_state["result"] = result_code
                            st.toast("Đã chuyển đổi xong!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}", icon="❌")

        # CỘT 2: OUTPUT LATEX CODE
        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
