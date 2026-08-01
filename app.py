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
            st.markdown("### 📥 Dữ liệu đầu vào & Yêu cầu")

            # 1. KHU VỰC DÁN CLIPBOARD (Sử dụng Javascript Event listener đồng bộ)
            st.caption("📋 **Dán ảnh từ Clipboard:** Click chọn ô bên dưới rồi bấm `Ctrl + V`")
            
            # Khung Paste sử dụng JavaScript truyền dữ liệu liên tục không bị mất state
            paste_html = """
            <div id="paste-box" contenteditable="true" style="
                border: 2px dashed #4F46E5;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                background-color: #F5F3FF;
                color: #4338CA;
                font-family: sans-serif;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                outline: none;
                min-height: 50px;
            ">
                📌 Click chọn ô này và bấm <b>Ctrl + V</b> để dán ảnh
            </div>

            <script>
            const box = document.getElementById('paste-box');
            box.addEventListener('paste', (e) => {
                e.preventDefault();
                const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                for (let item of items) {
                    if (item.type.indexOf('image') !== -1) {
                        const blob = item.getAsFile();
                        const reader = new FileReader();
                        reader.onload = function(event) {
                            const b64 = event.target.result;
                            window.parent.postMessage({
                                type: 'streamlit:setComponentValue',
                                value: b64
                            }, '*');
                        };
                        reader.readAsDataURL(blob);
                        
                        box.style.borderColor = '#10B981';
                        box.style.backgroundColor = '#ECFDF5';
                        box.style.color = '#047857';
                        box.innerHTML = '✅ Đã nhận ảnh! Thầy có thể dán tiếp ảnh khác...';
                        setTimeout(() => {
                            box.style.borderColor = '#4F46E5';
                            box.style.backgroundColor = '#F5F3FF';
                            box.style.color = '#4338CA';
                            box.innerHTML = '📌 Click chọn ô này và bấm <b>Ctrl + V</b> để dán ảnh';
                        }, 1500);
                        break;
                    }
                }
            });
            </script>
            """
            
            pasted_b64 = components.html(paste_html, height=70)

            # Xử lý NẠP VÀO SESSION STATE ngay khi phát hiện Base64 mới
            if pasted_b64 and isinstance(pasted_b64, str) and pasted_b64.startswith("data:image"):
                try:
                    _, encoded = pasted_b64.split(",", 1)
                    file_bytes = base64.b64decode(encoded)
                    
                    # Kiểm tra trùng lặp với ảnh cuối cùng
                    is_duplicate = False
                    if st.session_state["input_images"]:
                        last_bytes = st.session_state["input_images"][-1].get("bytes")
                        if last_bytes == file_bytes:
                            is_duplicate = True

                    if not is_duplicate:
                        preview_img = Image.open(io.BytesIO(file_bytes))
                        img_idx = len(st.session_state["input_images"]) + 1
                        st.session_state["input_images"].append({
                            "name": f"clipboard_{img_idx}.png",
                            "bytes": file_bytes,
                            "mime": "image/png",
                            "preview": preview_img
                        })
                        st.rerun()
                except Exception as e:
                    st.error(f"Lỗi đọc ảnh từ clipboard: {e}")

            st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

            # 2. KHU VỰC HIỂN THỊ PREVIEW CÁC ẢNH ĐÃ DÁN / UPLOAD (BẮT BUỘC HIỂN THỊ)
            if st.session_state["input_images"]:
                st.markdown(f"🖼️ **Ảnh đã dán/tải lên ({len(st.session_state['input_images'])}):**")
                
                # Hiển thị dạng lưới (Grid) 3 cột
                grid = st.columns(3)
                for idx, item in enumerate(list(st.session_state["input_images"])):
                    with grid[idx % 3]:
                        with st.container(border=True):
                            if item.get("preview"):
                                st.image(item["preview"], caption=item["name"], use_container_width=True)
                            elif item["mime"] == "application/pdf":
                                st.write(f"📄 `{item['name']}`")
                            
                            if st.button("🗑️ Xóa", key=f"del_btn_{idx}", use_container_width=True):
                                st.session_state["input_images"].pop(idx)
                                st.rerun()
            else:
                st.warning("⚠️ Chưa có ảnh nào trong danh sách. Hãy nhấn Ctrl+V ở ô trên hoặc bấm Upload.", icon="ℹ️")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # 3. EDITOR YÊU CẦU BỔ SUNG
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI",
                value=st.session_state["extra_notes_val"],
                height=90,
                placeholder="Nhập yêu cầu bổ sung cho AI...",
                label_visibility="collapsed"
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # 4. HÀNG NÚT THAO TÁC
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

            # Xử lý Upload file từ máy
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

            # Nút Xóa tất cả
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.rerun()

            # Nút Convert
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
