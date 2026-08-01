# app.py
import io
import json
import base64
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent

st.set_page_config(
    page_title="Math OCR Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def run(self):
        # 1. Khởi tạo Session State
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        api_key, mode, selected_model, add_solution = UIComponent.render_sidebar(api_service)
        
        api_service.api_key = api_key
        if api_key and not getattr(api_service, 'client', None):
            api_service.client = GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # ==================== CỘT 1: INPUT & CONTROLS ====================
        with col1:
            st.markdown("### 📥 Dữ liệu đầu vào")

            # Upload Native chuẩn xác, có thể Ctrl+V thẳng vào ô hoặc Kéo thả
            uploaded_files = st.file_uploader(
                "📄 **Chọn ảnh/PDF bài toán (Có thể nhấp vào ô rồi bấm Ctrl+V hoặc Kéo thả):**", 
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                accept_multiple_files=True,
                key="native_file_uploader"
            )

            # Xử lý dữ liệu đầu vào
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

            # Hiển thị Preview các ảnh đã chọn
            if current_inputs:
                st.markdown(f"🖼️ **Đã nhận {len(current_inputs)} tệp/ảnh:**")
                grid = st.columns(3)
                for idx, item in enumerate(current_inputs):
                    with grid[idx % 3]:
                        with st.container(border=True):
                            if item.get("preview"):
                                st.image(item["preview"], caption=item["name"], use_container_width=True)
                            else:
                                st.write(f"📄 `{item['name']}`")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- EDITOR YÊU CẦU BỔ SUNG ---
            st.caption("💡 **Yêu cầu bổ sung cho AI:**")
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

            # --- NÚT BẤM CHUYỂN ĐỔI ---
            btn_process = st.button("Convert sang LaTeX 🚀", type="primary", use_container_width=True)

            # Chạy Convert
            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not current_inputs:
                    st.error("Vui lòng chọn hoặc dán ít nhất 1 ảnh/file bài toán!", icon="⚠️")
                else:
                    with st.spinner("Đang chuyển đổi bài toán sang LaTeX..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            
                            result_code = processor.process(
                                input_data=current_inputs,
                                model=selected_model,
                                extra_prompt=extra_prompt,
                                add_solution=add_solution
                            )

                            st.session_state["result"] = result_code
                            st.toast("Chuyển đổi hoàn tất!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}", icon="❌")

        # ==================== CỘT 2: OUTPUT RESULT ====================
        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
