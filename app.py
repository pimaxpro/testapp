# app.py
import io
import streamlit as st
from PIL import Image
from streamlit_paste_button import paste_png
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
        if "paste_counter" not in st.session_state:
            st.session_state["paste_counter"] = 0

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

            # --- 1. NÚT DÁN ANH TỪ CLIPBOARD (NATIVE & BỀN VỮNG) ---
            st.caption("📋 **Dán ảnh từ Clipboard:** Nhấn nút bên dưới để dán ảnh vừa copy vào danh sách:")
            
            pasted_image = paste_png(
                label="📋 Click để dán ảnh từ Clipboard",
                text_color="#ffffff",
                background_color="#4F46E5",
                hover_background_color="#4338CA",
                key="clipboard_paster"
            )

            # Xử lý khi có dữ liệu ảnh dán vào
            if pasted_image.image_data is not None:
                # Chuyển image_data (PIL Image) sang Bytes để lưu bền vững
                img_pil = pasted_image.image_data
                buf = io.BytesIO()
                img_pil.save(buf, format="PNG")
                file_bytes = buf.getvalue()

                # Kiểm tra xem ảnh này đã được nạp vào danh sách chưa (chống lặp khi rerun)
                if not any(f.get("bytes") == file_bytes for f in st.session_state["input_images"]):
                    st.session_state["paste_counter"] += 1
                    img_name = f"clipboard_{st.session_state['paste_counter']}.png"
                    
                    st.session_state["input_images"].append({
                        "name": img_name,
                        "bytes": file_bytes,
                        "mime": "image/png",
                        "preview": img_pil
                    })
                    st.toast(f"Đã nhận {img_name}!", icon="✅")
                    st.rerun()

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

            # --- 2. KHU VỰC PREVIEW DANH SÁCH ẢNH ĐÃ DÁN / UPLOAD ---
            if st.session_state["input_images"]:
                st.markdown(f"🖼️ **Danh sách ảnh chuẩn bị xử lý ({len(st.session_state['input_images'])}):**")
                
                # Hiển thị dạng lưới (Grid) 3 cột có hình thu nhỏ
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
                st.info("💡 Chưa có ảnh nào. Thầy dán ảnh hoặc bấm Upload file ở bên dưới nhé.", icon="ℹ️")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- 3. EDITOR YÊU CẦU BỔ SUNG ---
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

            # --- 4. HÀNG NÚT THAO TÁC ---
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
