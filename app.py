import streamlit as st
from config import CUSTOM_CSS
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent

# Cấu hình Trang
st.set_page_config(page_title="Math OCR Pro - OOP Studio", page_icon="🧮", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    """Controller chính điều phối toàn bộ ứng dụng"""
    def __init__(self):
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = ""

    def run(self):
        UIComponent.render_header()
        
        # Khởi tạo API Service với API Key hiện tại
        api_service = GeminiAPIService(api_key=st.session_state.get("api_key", ""))
        
        # Render Sidebar & nhận thông số
        api_key, mode, selected_model, extra_prompt = UIComponent.render_sidebar(api_service)
        st.session_state["api_key"] = api_key
        
        # Cập nhật lại API Key nếu người dùng vừa nhập
        api_service.api_key = api_key
        if api_key:
            api_service.client = api_service.client or GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # CỘT 1: INPUT FILE (Hỗ trợ cả PNG, JPG, WEBP và PDF)
        with col1:
            st.markdown("### 📸 **1. Tải tài liệu đầu vào (Ảnh / PDF)**")
            uploaded_file = st.file_uploader(
                "Chọn file Ảnh hoặc tài liệu PDF đề thi", 
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                label_visibility="collapsed"
            )

            if uploaded_file:
                if uploaded_file.type == "application/pdf":
                    st.success(f"📄 Đã tải lên file PDF: **{uploaded_file.name}**")
                else:
                    st.image(uploaded_file, use_container_width=True)

                if st.button("🚀 Bắt đầu Xử lý & Chuyển đổi", type="primary", use_container_width=True):
                    if not api_key:
                        st.error("⚠️ Vui lòng nhập Gemini API Key ở Sidebar!")
                    else:
                        with st.spinner("⚡ Đang phân tích và xử lý mã LaTeX..."):
                            try:
                                # Dùng Factory để lấy Processor tương ứng
                                processor = ProcessorFactory.get_processor(mode, api_service)
                                
                                result_code = processor.process(
                                    file_bytes=uploaded_file.getvalue(),
                                    mime_type=uploaded_file.type,
                                    model=selected_model,
                                    extra_prompt=extra_prompt
                                )
                                st.session_state["result"] = result_code
                                st.toast("Xử lý thành công!", icon="✅")
                            except Exception as e:
                                st.error(f"❌ Lỗi xử lý: {e}")
            else:
                st.info("👆 Tải lên file ảnh hoặc file PDF chứa bài toán/đề thi để bắt đầu.")

        # CỘT 2: OUTPUT LATEX CODE
        with col2:
            st.markdown("### 📄 **2. Kết quả Mã LaTeX**")
            if "result" in st.session_state and st.session_state["result"]:
                latex_code = st.session_state["result"]
                
                # Hiển thị code với tính năng copy tích hợp
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
