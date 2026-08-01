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

# Giao diện phẳng tuyệt đối
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def run(self):
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []
        if "uploader_key" not in st.session_state:
            st.session_state["uploader_key"] = 0

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        # Nhận mode và tùy chọn lời giải trực tiếp từ Sidebar
        api_key, mode, selected_model, add_solution = UIComponent.render_sidebar(api_service)
        
        api_service.api_key = api_key
        if api_key and not getattr(api_service, 'client', None):
            api_service.client = GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # ==================== CỘT 1: INPUT & CONTROLS ====================
        with col1:
            st.markdown("### 📥 Dữ liệu đầu vào & Yêu cầu")
            
            # Danh sách ảnh/file đính kèm hiện tại
            if st.session_state.get("input_images"):
                st.caption(f"📷 Đã nhận **{len(st.session_state['input_images'])}** file/ảnh đầu vào:")
                num_files = len(st.session_state["input_images"])
                cols = st.columns(min(num_files, 4))
                
                for idx, item in enumerate(list(st.session_state["input_images"])):
                    with cols[idx % 4]:
                        with st.container(border=True):
                            if item["mime"] == "application/pdf":
                                st.write(f"📄 `{item['name'][:8]}`")
                            elif item.get("preview"):
                                st.image(item["preview"], use_container_width=True)
                            
                            if st.button("✖ Xóa", key=f"del_{idx}", use_container_width=True):
                                st.session_state["input_images"].pop(idx)
                                st.rerun()

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Editor yêu cầu bổ sung
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI",
                value=st.session_state["extra_notes_val"],
                height=110,
                placeholder="Nhập yêu cầu bổ sung cho AI...",
                label_visibility="collapsed"
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            # Hàng nút thao tác: Upload File, Dán Clipboard, Xóa tất cả, Convert
            act_col1, act_col2, act_col3 = st.columns([5, 3.5, 3.5])
            
            with act_col1:
                uploaded_files = st.file_uploader(
                    "Tải file ảnh/PDF", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed",
                    key=f"file_uploader_{st.session_state['uploader_key']}"
                )

            with act_col2:
                btn_clear_all = st.button("🗑️ Xóa tất cả", type="secondary", use_container_width=True)
                
            with act_col3:
                btn_process = st.button("Convert 🚀", type="primary", use_container_width=True)

            # --- KHU VỰC DÁN CLIPBOARD QUA JAVASCRIPT (HOẠT ĐỘNG TỐT TRÊN LINUX & CLOUD) ---
            st.caption("📋 **Dán ảnh từ Clipboard:** Nhấp vào ô bên dưới rồi nhấn `Ctrl + V` (hoặc `Cmd + V`)")
            clipboard_data = components.html(
                """
                <div id="paste-zone" style="
                    border: 2px dashed #999;
                    border-radius: 8px;
                    padding: 12px;
                    text-align: center;
                    color: #666;
                    font-family: sans-serif;
                    font-size: 13px;
                    cursor: pointer;
                    background-color: #fafafa;
                ">
                    📌 Click vào đây và nhấn <b>Ctrl + V</b> để dán ảnh
                </div>
                <script>
                const pasteZone = document.getElementById('paste-zone');
                document.addEventListener('paste', function(e) {
                    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                    for (let item of items) {
                        if (item.type.indexOf('image') !== -1) {
                            const blob = item.getAsFile();
                            const reader = new FileReader();
                            reader.onload = function(event) {
                                window.parent.postMessage({
                                    type: 'streamlit:setComponentValue',
                                    value: event.target.result
                                }, '*');
                            };
                            reader.readAsDataURL(blob);
                            pasteZone.innerHTML = "✅ Đã nhận ảnh từ Clipboard!";
                            pasteZone.style.borderColor = "#4CAF50";
                            break;
                        }
                    }
                });
                </script>
                """,
                height=65
            )

            # Xử lý dữ liệu Base64 nhận từ Clipboard JavaScript
            if clipboard_data and isinstance(clipboard_data, str) and clipboard_data.startswith("data:image"):
                try:
                    header, encoded = clipboard_data.split(",", 1)
                    file_bytes = base64.b64decode(encoded)
                    preview_img = Image.open(io.BytesIO(file_bytes))
                    
                    img_name = f"clipboard_{len(st.session_state['input_images']) + 1}.png"
                    
                    # Kiểm tra xem ảnh đã được thêm chưa để tránh trùng lặp khi rerun
                    if not any(item.get("bytes") == file_bytes for item in st.session_state["input_images"]):
                        st.session_state["input_images"].append({
                            "name": img_name,
                            "bytes": file_bytes,
                            "mime": "image/png",
                            "preview": preview_img
                        })
                        st.toast("Đã dán ảnh từ Clipboard thành công!", icon="📋")
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi khi xử lý ảnh dán: {e}", icon="❌")

            # Xử lý file upload
            if uploaded_files:
                has_new_file = False
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
                        has_new_file = True

                if has_new_file:
                    st.session_state["uploader_key"] += 1
                    st.rerun()

            # Sự kiện nút Xóa tất cả
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.rerun()

            # Sự kiện nút Convert
            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not st.session_state.get("input_images"):
                    st.error("Vui lòng tải file hoặc dán ảnh từ Clipboard!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý cấu trúc toán học..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            input_list = st.session_state.get("input_images", [])
                            
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
