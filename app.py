# app.py
import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent, AuthSystem

st.set_page_config(
    page_title="Math OCR Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def run(self):
        # 1. Khóa bảo vệ: Kiểm tra đăng nhập
        if not AuthSystem.check_auth():
            st.stop()  # Dừng ứng dụng nếu chưa đăng nhập thành công

        # 2. Khởi tạo API Key từ session state hoặc query params
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")

        # 3. Hiển thị thông tin người dùng & Nút đăng xuất ở Sidebar
        with st.sidebar:
            user_name = st.session_state.get('user_display', 'Người dùng')
            st.markdown(f"👤 **Tài khoản:** `{user_name}`")
            if st.button("🚪 Đăng xuất", use_container_width=True):
                st.session_state["authenticated"] = False
                st.rerun()
            st.markdown("---")

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        api_key, mode, selected_model, add_solution = UIComponent.render_sidebar(api_service)
        
        api_service.api_key = api_key
        if api_key and not getattr(api_service, 'client', None):
            api_service.client = GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        with col1:
            st.markdown("### Dữ liệu bài toán")
            
            # Sử dụng file_uploader chuẩn native
            uploaded_files = st.file_uploader(
                "Tải ảnh hoặc dán (Ctrl+V) / kéo thả vào đây",
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                accept_multiple_files=True,
                key="native_uploader"
            )

            current_inputs = []
            if uploaded_files:
                for file in uploaded_files:
                    file_bytes = file.getvalue()
                    mime_type = file.type
                    preview_img = Image.open(io.BytesIO(file_bytes)) if mime_type != "application/pdf" else None
                    current_inputs.append({
                        "name": file.name,
                        "bytes": file_bytes,
                        "mime": mime_type,
                        "preview": preview_img
                    })

            # Hiển thị preview rõ ràng từng ảnh
            if current_inputs:
                st.markdown(f"**Đã chọn ({len(current_inputs)} tệp):**")
                grid = st.columns(3)
                for idx, item in enumerate(current_inputs):
                    with grid[idx % 3]:
                        with st.container(border=True):
                            if item.get("preview"):
                                st.image(item["preview"], caption=item["name"], use_container_width=True)
                            else:
                                st.write(f"`{item['name']}`")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI",
                value=st.session_state["extra_notes_val"],
                height=90,
                placeholder="Nhập yêu cầu bổ sung...",
                label_visibility="collapsed"
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            btn_process = st.button("Convert 🚀", type="primary", use_container_width=True)

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="⚠️")
                elif not current_inputs:
                    st.error("Vui lòng chọn hoặc dán ảnh bài toán trước!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý cấu trúc toán học..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            
                            result_code = processor.process(
                                input_data=current_inputs,
                                model=selected_model,
                                extra_prompt=extra_prompt,
                                add_solution=add_solution
                            )

                            st.session_state["result"] = result_code
                            st.toast("Chuyển đổi hoàn tất!", icon="🎉")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}", icon="🚨")

        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
