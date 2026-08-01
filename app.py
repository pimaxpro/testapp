import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS
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
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    """Controller chính điều phối toàn bộ ứng dụng"""
    def __init__(self):
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = ""

    def run(self):
        UIComponent.render_header()
        
        api_service = GeminiAPIService(api_key=st.session_state.get("api_key", ""))
        api_key, mode, selected_model, extra_prompt = UIComponent.render_sidebar(api_service)
        
        st.session_state["api_key"] = api_key
        api_service.api_key = api_key
        if api_key:
            api_service.client = api_service.client or GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # CỘT 1: INPUT FILE / CLIPBOARD
        with col1:
            st.markdown("### 1. Tải hoặc Dán Ảnh (Ctrl+V) / PDF")
            
            # Đặt khu vực dán ảnh Clipboard lên trên
            paste_result = paste_image_button(
                label="📋 Dán ảnh từ Clipboard (Ctrl+V)",
                background_color="#4F46E5",
                text_color="#FFFFFF",
                hover_background_color="#3B82F6",
            )

            uploaded_file = st.file_uploader(
                "Hoặc chọn file Ảnh / PDF từ máy tính", 
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                label_visibility="visible"
            )

            file_bytes = None
            mime_type = None

            # Ưu tiên lấy từ Clipboard nếu người dùng vừa dán
            if paste_result.image_data is not None:
                st.info("Đã nhận ảnh từ Clipboard!")
                image = paste_result.image_data
                st.image(image, use_container_width=True)
                
                # Chuyển PIL Image sang bytes
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                file_bytes = buf.getvalue()
                mime_type = "image/png"

            # Nếu không dán ảnh thì kiểm tra File Uploader
            elif uploaded_file is not None:
                file_bytes = uploaded_file.getvalue()
                mime_type = uploaded_file.type
                
                if mime_type == "application/pdf":
                    st.success(f"Đã tải lên file PDF: **{uploaded_file.name}**", icon=":material/description:")
                else:
                    st.image(uploaded_file, use_container_width=True)

            # Nút thực thi
            if file_bytes:
                if st.button("Trích xuất & Chuyển đổi Mã", type="primary", use_container_width=True, icon=":material/rocket_launch:"):
                    if not api_key:
                        st.error("Vui lòng nhập Gemini API Key ở Sidebar!", icon=":material/warning:")
                    else:
                        with st.spinner("Đang phân tích và xử lý cấu trúc toán..."):
                            try:
                                processor = ProcessorFactory.get_processor(mode, api_service)
                                result_code = processor.process(
                                    file_bytes=file_bytes,
                                    mime_type=mime_type,
                                    model=selected_model,
                                    extra_prompt=extra_prompt
                                )
                                st.session_state["result"] = result_code
                                st.toast("Xử lý thành công!", icon="✅")
                            except Exception as e:
                                st.error(f"Lỗi xử lý: {e}", icon=":material/error:")
            else:
                st.info("Dán ảnh từ bộ nhớ tạm (Ctrl+V) hoặc chọn file để bắt đầu.", icon=":material/info:")

        # CỘT 2: OUTPUT LATEX CODE
        with col2:
            st.markdown("### 2. Mã LaTeX Trích Xuất")
            if "result" in st.session_state and st.session_state["result"]:
                latex_code = st.session_state["result"]
                
                if "\\begin{tkz" in latex_code or "\\begin{tikzpicture}" in latex_code:
                    st.warning("Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)", icon=":material/draw:")
                
                st.code(latex_code, language="latex")
                
                st.markdown("**Chỉnh sửa nhanh mã:**")
                st.text_area(
                    "Code Editor", 
                    value=latex_code, 
                    height=300, 
                    label_visibility="collapsed"
                )
            else:
                UIComponent.render_empty_state()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
