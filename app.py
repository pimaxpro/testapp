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

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def run(self):
        # 1. Khởi tạo Session State
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

            st.caption("📄 **Khung dán bài toán (Word Editor):** Click chuột vào khung bên dưới và bấm `Ctrl + V` để dán ảnh:")
            
            # Chuyển đổi các ảnh hiện tại sang base64 để truyền ngược lại cho Javascript render
            current_b64_list = []
            for item in st.session_state["input_images"]:
                if item.get("bytes"):
                    b64_data = base64.b64encode(item["bytes"]).decode("utf-8")
                    current_b64_list.append(f"data:{item['mime']};base64,{b64_data}")

            # Component HTML bắt sự kiện dán ảnh
            pasted_action = components.html(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.0/dist/streamlit-component-lib.js"></script>
                    <style>
                        body {{ margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }}
                        #editor-container {{
                            border: 2px dashed #818CF8;
                            border-radius: 10px;
                            background-color: #FFFFFF;
                            min-height: 150px;
                            padding: 12px;
                            outline: none;
                            box-sizing: border-box;
                        }}
                        #editor-container:focus-within {{
                            border-color: #4F46E5;
                            background-color: #FAFAFA;
                            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
                        }}
                        .placeholder {{
                            color: #94A3B8;
                            font-size: 14px;
                            font-weight: 500;
                            pointer-events: none;
                            text-align: center;
                            padding-top: 35px;
                        }}
                        #editor-content {{
                            outline: none;
                            min-height: 120px;
                            display: flex;
                            flex-wrap: wrap;
                            gap: 10px;
                            align-items: center;
                        }}
                        .pasted-img-wrapper {{
                            position: relative;
                            display: inline-block;
                        }}
                        .pasted-img-wrapper img {{
                            max-width: 200px;
                            max-height: 160px;
                            border-radius: 6px;
                            border: 1px solid #CBD5E1;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                            vertical-align: middle;
                        }}
                        .del-btn {{
                            position: absolute;
                            top: -6px;
                            right: -6px;
                            background: #EF4444;
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 22px;
                            height: 22px;
                            font-size: 14px;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-weight: bold;
                            line-height: 1;
                        }}
                    </style>
                </head>
                <body>
                    <div id="editor-container">
                        <div id="editor-content" contenteditable="true">
                            <div class="placeholder" id="ph">📋 Click chuột vào đây rồi nhấn <b>Ctrl + V</b> để DÁN ẢNH</div>
                        </div>
                    </div>

                    <script>
                        const container = document.getElementById('editor-container');
                        const content = document.getElementById('editor-content');
                        const ph = document.getElementById('ph');
                        const initialImages = {json.dumps(current_b64_list)};

                        function renderImages() {{
                            content.innerHTML = '';
                            if (initialImages.length === 0) {{
                                content.appendChild(ph);
                                ph.style.display = 'block';
                            }} else {{
                                initialImages.forEach((b64, idx) => {{
                                    createImgElement(b64, idx);
                                }});
                            }}
                            updateHeight();
                        }}

                        function updateHeight() {{
                            const h = Math.max(160, container.scrollHeight + 15);
                            Streamlit.setFrameHeight(h);
                        }}

                        function createImgElement(b64, index) {{
                            const wrapper = document.createElement('div');
                            wrapper.className = 'pasted-img-wrapper';
                            
                            const img = document.createElement('img');
                            img.src = b64;

                            const delBtn = document.createElement('button');
                            delBtn.className = 'del-btn';
                            delBtn.innerHTML = '&times;';
                            delBtn.onclick = (e) => {{
                                e.stopPropagation();
                                Streamlit.setComponentValue(JSON.stringify({{ action: 'DELETE', index: index }}));
                            }};

                            wrapper.appendChild(img);
                            wrapper.appendChild(delBtn);
                            content.appendChild(wrapper);
                        }}

                        window.addEventListener('load', () => {{
                            renderImages();
                        }});

                        content.addEventListener('focus', () => {{
                            if (initialImages.length === 0 && ph) {{
                                ph.style.display = 'none';
                            }}
                        }});

                        content.addEventListener('paste', (e) => {{
                            e.preventDefault();
                            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                            for (let item of items) {{
                                if (item.type.indexOf('image') !== -1) {{
                                    const file = item.getAsFile();
                                    const reader = new FileReader();
                                    reader.onload = (evt) => {{
                                        const b64 = evt.target.result;
                                        Streamlit.setComponentValue(JSON.stringify({{ action: 'ADD', data: b64 }}));
                                    }};
                                    reader.readAsDataURL(file);
                                    break;
                                }}
                            }}
                        }});
                    </script>
                </body>
                </html>
                """,
                height=165
            )

            # Xử lý sự kiện ADD / DELETE ảnh từ Editor truyền về Python
            if pasted_action:
                try:
                    event = json.loads(pasted_action)
                    if event.get("action") == "ADD":
                        b64_str = event.get("data", "")
                        if b64_str.startswith("data:image"):
                            header, encoded = b64_str.split(",", 1)
                            file_bytes = base64.b64decode(encoded)
                            img_count = len(st.session_state["input_images"]) + 1
                            st.session_state["input_images"].append({
                                "name": f"Pasted_Image_{img_count}.png",
                                "bytes": file_bytes,
                                "mime": "image/png"
                            })
                            st.rerun()
                    elif event.get("action") == "DELETE":
                        idx = event.get("index")
                        if idx is not None and 0 <= idx < len(st.session_state["input_images"]):
                            st.session_state["input_images"].pop(idx)
                            st.rerun()
                except Exception:
                    pass

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

            # Upload file từ máy
            if uploaded_files:
                has_new = False
                for file in uploaded_files:
                    file_bytes = file.getvalue()
                    mime_type = file.type
                    if not any(f.get("name") == file.name for f in st.session_state["input_images"]):
                        st.session_state["input_images"].append({
                            "name": file.name,
                            "bytes": file_bytes,
                            "mime": mime_type
                        })
                        has_new = True
                if has_new:
                    st.session_state["uploader_key"] += 1
                    st.rerun()

            # Xóa sạch
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.session_state["uploader_key"] += 1
                st.rerun()

            # Chạy Convert
            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not st.session_state["input_images"]:
                    st.error("Vui lòng dán ảnh vào khung Word Editor hoặc chọn file ở bên dưới!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý cấu trúc toán học..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            
                            result_code = processor.process(
                                input_data=st.session_state["input_images"],
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
