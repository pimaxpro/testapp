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
        # 1. Khởi tạo kho lưu trữ ảnh dán trong Session State
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
            st.markdown("### 📥 Dữ liệu bài toán")
            st.caption("📋 **Khung dán ảnh:** Click vào khung bên dưới và bấm `Ctrl + V` (dán bao nhiêu ảnh cũng được):")

            # --- KHUNG DÁN ẢNH CÓ LƯU STATE TRỰC TIẾP ---
            # Chuyển các ảnh hiện có trong state thành mảng base64 để hiển thị lên khung
            existing_b64 = []
            for item in st.session_state["input_images"]:
                b64_str = base64.b64encode(item["bytes"]).decode("utf-8")
                existing_b64.append(f"data:{item['mime']};base64,{b64_str}")

            paste_component = components.html(
                f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.0/dist/streamlit-component-lib.js"></script>
                    <style>
                        body {{ margin: 0; padding: 0; font-family: sans-serif; }}
                        #paste-box {{
                            border: 2px dashed #6366F1;
                            border-radius: 10px;
                            background-color: #FAFAFA;
                            min-height: 140px;
                            padding: 12px;
                            outline: none;
                            display: flex;
                            flex-wrap: wrap;
                            gap: 10px;
                            align-items: center;
                            justify-content: center;
                            box-sizing: border-box;
                            cursor: pointer;
                        }}
                        #paste-box:focus {{
                            border-color: #4F46E5;
                            background-color: #EEF2FF;
                        }}
                        .placeholder {{
                            color: #94A3B8;
                            font-size: 14px;
                            font-weight: 600;
                            text-align: center;
                            pointer-events: none;
                        }}
                        .img-card {{
                            position: relative;
                            display: inline-block;
                        }}
                        .img-card img {{
                            max-width: 140px;
                            max-height: 120px;
                            border-radius: 6px;
                            border: 1px solid #CBD5E1;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                        }}
                        .del-x {{
                            position: absolute;
                            top: -6px;
                            right: -6px;
                            background: #EF4444;
                            color: white;
                            border: none;
                            border-radius: 50%;
                            width: 20px;
                            height: 20px;
                            font-size: 12px;
                            font-weight: bold;
                            cursor: pointer;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }}
                    </style>
                </head>
                <body>
                    <div id="paste-box" tabindex="0">
                        <div class="placeholder" id="ph">📋 Click chuột vào đây và bấm <b>Ctrl + V</b> để dán ảnh</div>
                    </div>

                    <script>
                        const box = document.getElementById('paste-box');
                        const ph = document.getElementById('ph');
                        let images = {json.dumps(existing_b64)};

                        function render() {{
                            // Giữ lại placeholder nếu chưa có ảnh
                            box.innerHTML = '';
                            if (images.length === 0) {{
                                box.appendChild(ph);
                                ph.style.display = 'block';
                            }} else {{
                                images.forEach((b64, idx) => {{
                                    const card = document.createElement('div');
                                    card.className = 'img-card';

                                    const img = document.createElement('img');
                                    img.src = b64;

                                    const btn = document.createElement('button');
                                    btn.className = 'del-x';
                                    btn.innerHTML = '&times;';
                                    btn.onclick = (e) => {{
                                        e.stopPropagation();
                                        images.splice(idx, 1);
                                        Streamlit.setComponentValue(JSON.stringify({{ type: 'UPDATE', data: images }}));
                                    }};

                                    card.appendChild(img);
                                    card.appendChild(btn);
                                    box.appendChild(card);
                                }});
                            }}
                            const h = Math.max(160, box.scrollHeight + 15);
                            Streamlit.setFrameHeight(h);
                        }}

                        window.addEventListener('load', () => {{
                            render();
                        }});

                        box.addEventListener('paste', (e) => {{
                            e.preventDefault();
                            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                            for (let item of items) {{
                                if (item.type.indexOf('image') !== -1) {{
                                    const file = item.getAsFile();
                                    const reader = new FileReader();
                                    reader.onload = (evt) => {{
                                        images.push(evt.target.result);
                                        Streamlit.setComponentValue(JSON.stringify({{ type: 'UPDATE', data: images }}));
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

            # Đồng bộ dữ liệu từ khung dán HTML về Session State của Python
            if paste_component:
                try:
                    payload = json.loads(paste_component)
                    if payload.get("type") == "UPDATE":
                        b64_list = payload.get("data", [])
                        new_images = []
                        for idx, b64_str in enumerate(b64_list):
                            if b64_str.startswith("data:image"):
                                _, encoded = b64_str.split(",", 1)
                                file_bytes = base64.b64decode(encoded)
                                new_images.append({
                                    "name": f"Pasted_Image_{idx+1}.png",
                                    "bytes": file_bytes,
                                    "mime": "image/png"
                                })
                        # Chỉ rerun nếu danh sách thực sự thay đổi để tránh vòng lặp
                        if len(new_images) != len(st.session_state["input_images"]):
                            st.session_state["input_images"] = new_images
                            st.rerun()
                except Exception:
                    pass

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

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

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- HÀNG NÚT THAO TÁC ---
            act_col1, act_col2, act_col3 = st.columns([5, 3.5, 3.5])
            
            with act_col1:
                uploaded_files = st.file_uploader(
                    "Hoặc tải file từ máy", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed"
                )

            with act_col2:
                btn_clear_all = st.button("🗑️ Xóa tất cả", type="secondary", use_container_width=True)
                
            with act_col3:
                btn_process = st.button("Convert 🚀", type="primary", use_container_width=True)

            # Bổ sung file nếu tải từ máy tính
            all_process_images = list(st.session_state["input_images"])
            if uploaded_files:
                for file in uploaded_files:
                    file_bytes = file.getvalue()
                    if not any(f["bytes"] == file_bytes for f in all_process_images):
                        all_process_images.append({
                            "name": file.name,
                            "bytes": file_bytes,
                            "mime": file.type
                        })

            # Nút Xóa tất cả
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.rerun()

            # --- SỰ KIỆN KHI BẤM NÚT "CONVERT 🚀" ---
            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not all_process_images:
                    st.error("Vui lòng dán ảnh vào khung hoặc chọn file từ máy trước khi bấm Convert!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý cấu trúc toán học..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            
                            result_code = processor.process(
                                input_data=all_process_images,
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
