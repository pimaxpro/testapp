# app.py
import io
import json
import base64
import streamlit as st
import streamlit.components.v1 as components
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

# Giao diện phẳng
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def run(self):
        # Khởi tạo Session State
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []
        if "uploader_key" not in st.session_state:
            st.session_state["uploader_key"] = 0

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

            # --- KHUNG EDITOR DÁN ẢNH DẠNG WORD / NOTION ---
            st.caption("📄 **Khung dán bài toán:** Click chuột vào vùng bên dưới và nhấn `Ctrl + V` để dán ảnh (dán bao nhiêu ảnh tùy thích):")
            
            word_editor_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.0/dist/streamlit-component-lib.js"></script>
                <style>
                    body { margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }
                    #editor {
                        border: 1px solid #CBD5E1;
                        border-radius: 8px;
                        background-color: #FFFFFF;
                        min-height: 140px;
                        padding: 12px;
                        outline: none;
                        font-size: 14px;
                        color: #64748B;
                        box-sizing: border-box;
                    }
                    #editor:focus {
                        border-color: #4F46E5;
                        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
                    }
                    #editor img {
                        max-width: 180px;
                        max-height: 140px;
                        margin: 6px;
                        border-radius: 6px;
                        border: 1px solid #E2E8F0;
                        vertical-align: middle;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    .placeholder {
                        color: #94A3B8;
                        pointer-events: none;
                    }
                </style>
            </head>
            <body>
                <div id="editor" contenteditable="true">
                    <span class="placeholder">Click vào đây và nhấn <b>Ctrl + V</b> để dán ảnh vào bài làm...</span>
                </div>

                <script>
                    const editor = document.getElementById('editor');
                    let images = [];

                    function updateHeight() {
                        const h = Math.max(150, editor.scrollHeight + 10);
                        Streamlit.setFrameHeight(h);
                    }

                    window.addEventListener('load', () => {
                        updateHeight();
                    });

                    editor.addEventListener('focus', () => {
                        const placeholder = editor.querySelector('.placeholder');
                        if (placeholder) {
                            placeholder.remove();
                        }
                    });

                    editor.addEventListener('paste', (e) => {
                        e.preventDefault();
                        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                        for (let item of items) {
                            if (item.type.indexOf('image') !== -1) {
                                const file = item.getAsFile();
                                const reader = new FileReader();
                                reader.onload = (evt) => {
                                    const b64 = evt.target.result;
                                    
                                    // Tạo thẻ img hiển thị trực tiếp trong editor như Word
                                    const imgNode = document.createElement('img');
                                    imgNode.src = b64;
                                    editor.appendChild(imgNode);
                                    
                                    images.push(b64);
                                    
                                    // Báo dữ liệu về cho Streamlit
                                    Streamlit.setComponentValue(JSON.stringify(images));
                                    updateHeight();
                                };
                                reader.readAsDataURL(file);
                            }
                        }
                    });
                </script>
            </body>
            </html>
            """

            pasted_json = components.html(word_editor_html, height=160)

            # Đọc danh sách ảnh dán trực tiếp từ Editor
            pasted_b64_list = []
            if pasted_json:
                try:
                    pasted_b64_list = json.loads(pasted_json)
                except Exception:
                    pasted_b64_list = []

            # Nạp danh sách ảnh từ Editor vào mảng dữ liệu gửi AI
            current_pasted_images = []
            for idx, b64_str in enumerate(pasted_b64_list):
                if b64_str.startswith("data:image"):
                    _, encoded = b64_str.split(",", 1)
                    file_bytes = base64.b64decode(encoded)
                    preview_img = Image.open(io.BytesIO(file_bytes))
                    current_pasted_images.append({
                        "name": f"Pasted_Image_{idx+1}.png",
                        "bytes": file_bytes,
                        "mime": "image/png",
                        "preview": preview_img
                    })

            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

            # --- EDITOR YÊU CẦU BỔ SUNG ---
            st.caption("💡 **Yêu cầu bổ sung cho AI:**")
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI",
                value=st.session_state["extra_notes_val"],
                height=85,
                placeholder="Nhập yêu cầu bổ sung...",
                label_visibility="collapsed"
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # --- HÀNG NÚT THAO TÁC UPLOAD & CONVERT ---
            act_col1, act_col2, act_col3 = st.columns([5, 3.5, 3.5])
            
            with act_col1:
                uploaded_files = st.file_uploader(
                    "Tải file từ máy", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                    key=f"file_uploader_{st.session_state['uploader_key']}"
                )

            with act_col2:
                btn_clear_all = st.button("🗑️ Xóa tất cả", type="secondary", use_container_width=True)
                
            with act_col3:
                btn_process = st.button("Convert 🚀", type="primary", use_container_width=True)

            # Tổng hợp toàn bộ ảnh (từ Khung dán Word + File Upload)
            all_images = list(current_pasted_images)
            if uploaded_files:
                for file in uploaded_files:
                    file_bytes = file.getvalue()
                    mime_type = file.type
                    if not any(f.get("name") == file.name for f in all_images):
                        preview_img = Image.open(io.BytesIO(file_bytes)) if mime_type != "application/pdf" else None
                        all_images.append({
                            "name": file.name,
                            "bytes": file_bytes,
                            "mime": mime_type,
                            "preview": preview_img
                        })

            # Xóa sạch
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.session_state["uploader_key"] += 1
                st.rerun()

            # Chạy Convert
            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not all_images:
                    st.error("Vui lòng dán ảnh vào khung Word Editor hoặc chọn file ở bên dưới!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý cấu trúc toán học..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            
                            result_code = processor.process(
                                input_data=all_images,
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
