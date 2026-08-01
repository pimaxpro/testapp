# app.py
import io
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
        # 1. Khởi tạo Session State
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []
        if "uploader_key" not in st.session_state:
            st.session_state["uploader_key"] = 0
        if "last_paste_id" not in st.session_state:
            st.session_state["last_paste_id"] = ""

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
            st.markdown("### 📥 Dữ liệu đầu vào & Yêu cầu")

            # --- KHU VỰC DÁN CLIPBOARD NATIVE (DÙNG STREAMLIT SDK CHUẨN) ---
            st.caption("📋 **Dán ảnh từ Clipboard:** Nhấp vào khung bên dưới rồi bấm `Ctrl + V`:")
            
            pasted_data = components.html(
                """
                <!DOCTYPE html>
                <html>
                <head>
                    <script src="https://cdn.jsdelivr.net/npm/streamlit-component-lib@1.4.0/dist/streamlit-component-lib.js"></script>
                    <style>
                        body { margin: 0; padding: 0; font-family: sans-serif; }
                        #paste-zone {
                            border: 2px dashed #6366F1;
                            border-radius: 8px;
                            background-color: #EEF2FF;
                            color: #4338CA;
                            padding: 14px;
                            text-align: center;
                            font-weight: 600;
                            font-size: 14px;
                            cursor: pointer;
                            outline: none;
                            user-select: none;
                        }
                        #paste-zone:focus {
                            border-color: #4338CA;
                            background-color: #E0E7FF;
                        }
                    </style>
                </head>
                <body>
                    <div id="paste-zone" tabindex="0">
                        📋 BẤM VÀO ĐÂY RỒI NHẤN CTRL + V ĐỂ DÁN ẢNH
                    </div>

                    <script>
                        const zone = document.getElementById('paste-zone');
                        
                        // Tự động focus khi load
                        window.addEventListener('load', () => {
                            zone.focus();
                            Streamlit.setFrameHeight(60);
                        });

                        zone.addEventListener('paste', (e) => {
                            e.preventDefault();
                            const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                            for (let item of items) {
                                if (item.type.indexOf('image') !== -1) {
                                    const file = item.getAsFile();
                                    const reader = new FileReader();
                                    reader.onload = (evt) => {
                                        const b64 = evt.target.result;
                                        // Gửi dữ liệu về Python qua Streamlit SDK chuẩn
                                        const payload = JSON.stringify({
                                            id: Date.now(),
                                            data: b64
                                        });
                                        Streamlit.setComponentValue(payload);
                                    };
                                    reader.readAsDataURL(file);
                                    
                                    zone.style.backgroundColor = '#D1FAE5';
                                    zone.style.borderColor = '#10B981';
                                    zone.style.color = '#065F46';
                                    zone.innerText = '✅ Đã nhận ảnh! Thầy có thể Ctrl + V tiếp...';
                                    setTimeout(() => {
                                        zone.style.backgroundColor = '#EEF2FF';
                                        zone.style.borderColor = '#6366F1';
                                        zone.style.color = '#4338CA';
                                        zone.innerText = '📋 BẤM VÀO ĐÂY RỒI NHẤN CTRL + V ĐỂ DÁN ẢNH';
                                    }, 1000);
                                    break;
                                }
                            }
                        });
                    </script>
                </body>
                </html>
                """,
                height=65
            )

            # Xử lý khi nhận dữ liệu dán từ Javascript
            if pasted_data:
                try:
                    import json
                    parsed = json.loads(pasted_data)
                    paste_id = str(parsed.get("id"))
                    b64_str = parsed.get("data", "")

                    if paste_id != st.session_state["last_paste_id"] and b64_str.startswith("data:image"):
                        st.session_state["last_paste_id"] = paste_id
                        header, encoded = b64_str.split(",", 1)
                        file_bytes = base64.b64decode(encoded)
                        preview_img = Image.open(io.BytesIO(file_bytes))
                        
                        img_num = len(st.session_state["input_images"]) + 1
                        st.session_state["input_images"].append({
                            "name": f"Clipboard_{img_num}.png",
                            "bytes": file_bytes,
                            "mime": "image/png",
                            "preview": preview_img
                        })
                        st.rerun()
                except Exception as e:
                    pass

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

            # --- PREVIEW DANH SÁCH ẢNH ĐÃ DÁN / UPLOAD ---
            if st.session_state["input_images"]:
                st.markdown(f"🖼️ **Ảnh chờ xử lý ({len(st.session_state['input_images'])}):**")
                grid = st.columns(3)
                for idx, item in enumerate(list(st.session_state["input_images"])):
                    with grid[idx % 3]:
                        with st.container(border=True):
                            if item.get("preview"):
                                st.image(item["preview"], caption=item["name"], use_container_width=True)
                            elif item["mime"] == "application/pdf":
                                st.write(f"📄 `{item['name']}`")
                            
                            if st.button("🗑️ Xóa", key=f"del_img_{idx}", use_container_width=True):
                                st.session_state["input_images"].pop(idx)
                                st.rerun()
            else:
                st.info("Chưa có ảnh nào. Thầy click vào ô xanh nhạt ở trên rồi bấm **Ctrl + V** nhé.", icon="ℹ️")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- EDITOR YÊU CẦU BỔ SUNG ---
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

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- HÀNG NÚT THAO TÁC ---
            act_col1, act_col2, act_col3 = st.columns([5, 3.5, 3.5])
            
            with act_col1:
                uploaded_files = st.file_uploader(
                    "Hoặc chọn file từ máy", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                    key=f"file_uploader_{st.session_state['uploader_key']}"
                )

            with act_col2:
                btn_clear_all = st.button("🗑️ Xóa tất cả", type="secondary", use_container_width=True)
                
            with act_col3:
                btn_process = st.button("Convert 🚀", type="primary", use_container_width=True)

            # Tải file từ máy
            if uploaded_files:
                has_new = False
                for file in uploaded_files:
                    file_bytes = file.getvalue()
                    mime_type = file.type
                    if not any(f.get("name") == file.name for f in st.session_state["input_images"]):
                        preview_img = Image.open(io.BytesIO(file_bytes)) if mime_type != "application/pdf" else None
                        st.session_state["input_images"].append({
                            "name": file.name,
                            "bytes": file_bytes,
                            "mime": mime_type,
                            "preview": preview_img
                        })
                        has_new = True
                if has_new:
                    st.session_state["uploader_key"] += 1
                    st.rerun()

            # Xóa sạch danh sách
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.session_state["last_paste_id"] = ""
                st.rerun()

            # Chạy Convert
            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not st.session_state["input_images"]:
                    st.error("Vui lòng dán ảnh hoặc tải file lên trước!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý cấu trúc toán học..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            input_list = st.session_state["input_images"]
                            
                            result_code = processor.process(
                                input_data=input_list,
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
