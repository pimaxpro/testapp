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
        # 1. Kiểm tra đăng nhập
        if not AuthSystem.check_auth():
            st.stop()

        # 2. Khởi tạo API Key từ session state
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")

        # 3. Sidebar - Thông tin tài khoản & Nút Đăng xuất trên 1 hàng
        with st.sidebar:
            col_usr, col_logout = st.columns([6, 4], vertical_alignment="center")
            with col_usr:
                user_name = st.session_state.get('user_display', 'Người dùng')
                st.markdown(f"👤 **`{user_name}`**")
            with col_logout:
                if st.button("Đăng xuất", use_container_width=True):
                    # --- CHÈN THÊM: Gọi hàm logout để xóa cả cookie ---
                    AuthSystem.logout()
                    st.rerun()

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        # Render Sidebar & nhận cấu hình
        api_key, mode, selected_model, add_solution = UIComponent.render_sidebar(api_service)

        col1, col2 = st.columns([5, 7], gap="large")

        with col1:
            st.markdown("### Dữ liệu bài toán")
            
            uploaded_files = st.file_uploader(
                "Tải ảnh hoặc dán (Ctrl+V) / kéo thả vào đây",
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                accept_multiple_files=True,
                key="native_uploader"
            )

            # --- BẮT ĐẦU PHẦN CHÈN THÊM: Tính năng dán nhiều ảnh từ Clipboard ---
            # Khởi tạo state để lưu trữ danh sách ảnh được dán và hash để tránh dán đúp
            if "pasted_items" not in st.session_state:
                st.session_state["pasted_items"] = []
            if "pasted_hashes" not in st.session_state:
                st.session_state["pasted_hashes"] = set()

            try:
                from streamlit_paste_button import paste_image_button
                
                col_btn1, col_btn2 = st.columns([6, 4])
                with col_btn1:
                    paste_result = paste_image_button(
                        label="📋 Nhấn vào đây và Ctrl+V để dán ảnh",
                        text_color="#ffffff",
                        background_color="#4F46E5",
                        hover_background_color="#3730A3"
                    )
                with col_btn2:
                    if st.session_state["pasted_items"]:
                        if st.button("🗑️ Xóa ảnh dán", use_container_width=True):
                            st.session_state["pasted_items"] = []
                            st.session_state["pasted_hashes"] = set()
                            st.rerun()

                # Xử lý khi có ảnh mới được dán
                if paste_result.image_data is not None:
                    # Chuyển đổi PIL Image sang bytes
                    img_byte_arr = io.BytesIO()
                    paste_result.image_data.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    
                    # Dùng hash để nhận diện ảnh, tránh trường hợp re-run bị cộng dồn ảnh cũ
                    img_hash = hash(img_bytes)

                    if img_hash not in st.session_state["pasted_hashes"]:
                        st.session_state["pasted_hashes"].add(img_hash)
                        idx = len(st.session_state["pasted_items"]) + 1
                        st.session_state["pasted_items"].append({
                            "name": f"Pasted_Image_{idx}.png",
                            "bytes": img_bytes,
                            "mime": "image/png",
                            "preview": paste_result.image_data
                        })
                        st.rerun() # Rerun ngay để UI cập nhật grid hiển thị ảnh
            except ImportError:
                st.warning("Gợi ý: Cài đặt thư viện `streamlit-paste-button` để dùng tính năng dán ảnh (đã có trong requirements).")
            # --- KẾT THÚC PHẦN CHÈN THÊM ---

            current_inputs = []
            
            # 1. Thêm các ảnh từ uploader mặc định
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
            
            # 2. Thêm các ảnh đã dán từ Clipboard vào chung danh sách
            if st.session_state["pasted_items"]:
                current_inputs.extend(st.session_state["pasted_items"])

            # Hiển thị Grid xem trước tất cả các ảnh (Cả Upload và Paste)
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
                    st.error("Vui lòng chọn hoặc nhập API Key ở thanh bên!", icon="⚠️")
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
