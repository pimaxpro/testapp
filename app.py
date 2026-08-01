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
        # Khởi tạo Session State chuẩn
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []
        if "uploader_key" not in st.session_state:
            st.session_state["uploader_key"] = 0
        if "last_pasted_raw" not in st.session_state:
            st.session_state["last_pasted_raw"] = None

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

            # --- KHU VỰC DÁN CLIPBOARD CÓ PREVIEW TỨC THÌ & HỖ TRỢ DÁN NHIỀU ẢNH ---
            st.caption("📋 **Dán ảnh từ Clipboard:** Click vào ô bên dưới rồi bấm `Ctrl + V` (có thể dán liên tiếp nhiều ảnh):")
            
            # Component JS tự chứa xem trước (Preview) & gửi dữ liệu lên Streamlit
            paste_component = components.html(
                """
                <div id="drop-zone" style="
                    border: 2px dashed #4F46E5;
                    border-radius: 8px;
                    padding: 12px;
                    text-align: center;
                    background-color: #F5F3FF;
                    color: #4338CA;
                    font-family: sans-serif;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    outline: none;
                " tabindex="0">
                    📌 Nhấp vào đây & bấm <b>Ctrl + V</b> để dán ảnh
                </div>

                <script>
                const zone = document.getElementById('drop-zone');

                zone.addEventListener('paste', (e) => {
                    const items = (e.clipboardData || e.originalEvent.clipboardData).items;
                    for (let item of items) {
                        if (item.type.indexOf('image') !== -1) {
                            const blob = item.getAsFile();
                            const reader = new FileReader();
                            reader.onload = function(event) {
                                const b64 = event.target.result;
                                // Gửi về Streamlit
                                window.parent.postMessage({
                                    type: 'streamlit:setComponentValue',
                                    value: b64 + '||' + Date.now()
                                }, '*');
                            };
                            reader.readAsDataURL(blob);
                            
                            zone.style.borderColor = '#10B981';
                            zone.style.backgroundColor = '#ECFDF5';
                            zone.style.color = '#047857';
                            zone.innerHTML = '✅ Đã nhận ảnh! Bấm Ctrl+V để dán tiếp...';
                            
                            setTimeout(() => {
                                zone.style.borderColor = '#4F46E5';
                                zone.style.backgroundColor = '#F5F3FF';
                                zone.style.color = '#4338CA';
                                zone.innerHTML = '📌 Nhấp vào đây & bấm <b>Ctrl + V</b> để dán ảnh';
                            }, 1200);
                            break;
                        }
                    }
                });
                </script>
                """,
                height=65
            )

            # Xử lý bẫy lưu ảnh dán vào State
            if paste_component and isinstance(paste_component, str) and "||" in paste_component:
                if paste_component != st.session_state["last_pasted_raw"]:
                    st.session_state["last_pasted_raw"] = paste_component
                    raw_b64, _ = paste_component.split("||", 1)
                    
                    if raw_b64.startswith("data:image"):
                        try:
                            _, encoded = raw_b64.split(",", 1)
                            file_bytes = base64.b64decode(encoded)
                            preview_img = Image.open(io.BytesIO(file_bytes))
                            
                            img_count = len(st.session_state["input_images"]) + 1
                            st.session_state["input_images"].append({
                                "name": f"clipboard_img_{img_count}.png",
                                "bytes": file_bytes,
                                "mime": "image/png",
                                "preview": preview_img
                            })
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi đọc ảnh: {e}")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # --- KHU VỰC HIỂN THỊ PREVIEW TOÀN BỘ CÁC ẢNH ĐÃ DÁN / UPLOAD ---
            if st.session_state["input_images"]:
                st.write(f"📷 **Danh sách ảnh đã dán ({len(st.session_state['input_images'])} ảnh):**")
                
                # Tạo lưới xem trước hình ảnh
                grid_cols = st.columns(min(len(st.session_state["input_images"]), 4))
                for idx, item in enumerate(list(st.session_state["input_images"])):
                    with grid_cols[idx % 4]:
                        with st.container(border=True):
                            if item.get("preview"):
                                st.image(item["preview"], caption=item["name"], use_container_width=True)
                            elif item["mime"] == "application/pdf":
                                st.write(f"📄 `{item['name'][:10]}`")
                            
                            if st.button("✖ Xóa", key=f"del_img_{idx}", use_container_width=True):
                                st.session_state["input_images"].pop(idx)
                                st.rerun()
            else:
                st.info("Chưa có ảnh nào được dán hoặc tải lên.", icon="ℹ️")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Editor yêu cầu bổ sung
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

            # Hàng nút thao tác
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

            # Xử lý file Upload thêm
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

            if btn_clear_all:
                st.session_state["input_images"] = []
                st.session_state["last_pasted_raw"] = None
                st.rerun()

            # Sự kiện Convert
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
