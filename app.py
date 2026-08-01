import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent
from streamlit_paste_button import paste_image_button

st.set_page_config(
    page_title="Math OCR Pro - OOP Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

class MathOCRApp:
    """Controller chính điều phối toàn bộ ứng dụng"""
    def __init__(self):
        pass

    def run(self):
        # KHỞI TẠO SESSION STATE AN TOÀN
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        # SIDEBAR
        api_key, mode, selected_model = UIComponent.render_sidebar(api_service)
        
        api_service.api_key = api_key
        if api_key and not getattr(api_service, 'client', None):
            api_service.client = GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # CỘT 1: INPUT FILE / CLIPBOARD
        with col1:
            st.markdown("### 1. Dữ liệu đầu vào")
            
            # --- ĐẶT 2 NÚT NẮM CÙNG 1 HÀNG ---
            in_col1, in_col2 = st.columns(2)

            with in_col1:
                paste_result = paste_image_button(
                    label="📋 Dán từ Clipboard",
                    background_color="#4F46E5",
                    text_color="#FFFFFF",
                    hover_background_color="#3B82F6",
                )

            with in_col2:
                uploaded_files = st.file_uploader(
                    "Chọn file Ảnh / PDF", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed"  # Ẩn bớt nhãn thừa để 2 nút cân bằng hơn
                )

            # Xử lý khi dán ảnh từ Clipboard
            if paste_result.image_data is not None:
                image = paste_result.image_data
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_bytes = buf.getvalue()
                
                if "last_pasted" not in st.session_state or st.session_state["last_pasted"] != img_bytes:
                    st.session_state["last_pasted"] = img_bytes
                    st.session_state["input_images"].append({
                        "name": f"Clipboard_Image_{len(st.session_state['input_images']) + 1}.png",
                        "bytes": img_bytes,
                        "mime": "image/png",
                        "preview": image
                    })
                    st.toast("Đã thêm ảnh từ Clipboard!", icon="📋")

            # Xử lý các file từ file_uploader
            if uploaded_files:
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

            # Hiển thị box danh sách các file/ảnh đã nhận
            if st.session_state.get("input_images"):
                st.caption(f"📸 Đã nhận **{len(st.session_state['input_images'])}** tệp đầu vào:")
                cols = st.columns(min(len(st.session_state["input_images"]), 4))
                for idx, item in enumerate(st.session_state["input_images"]):
                    with cols[idx % 4]:
                        if item["mime"] == "application/pdf":
                            st.info(f"📄 {item['name']}")
                        elif item.get("preview"):
                            st.image(item["preview"], use_container_width=True, caption=f"Ảnh {idx + 1}")

            st.markdown("---")

            # BOX YÊU CẦU BỔ SUNG CHO CON AI
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "💡 Yêu cầu bổ sung cho con AI", 
                value=st.session_state["extra_notes_val"],
                height=120,
                help="Nhập thêm quy định định dạng hoặc lưu ý đặc biệt cho bài toán."
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("---")

            # 2 NÚT THỰC THI (TRÍCH XUẤT / XÓA) ĐẶT CÙNG HÀNG
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                btn_process = st.button(
                    "🚀 Trích xuất & Chuyển đổi", 
                    type="primary", 
                    use_container_width=True
                )
            with btn_col2:
                btn_clear = st.button(
                    "🗑️ Xóa danh sách ảnh", 
                    type="secondary", 
                    use_container_width=True
                )

            if btn_clear:
                st.session_state["input_images"] = []
                if "last_pasted" in st.session_state:
                    del st.session_state["last_pasted"]
                st.rerun()

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập Gemini API Key ở Sidebar!", icon=":material/warning:")
                elif not st.session_state.get("input_images"):
                    st.error("Vui lòng dán hoặc tải lên ít nhất 1 ảnh/PDF!", icon=":material/image:")
                else:
                    with st.spinner("Đang phân tích và xử lý cấu trúc toán..."):
                        try:
                            processor = ProcessorFactory.get_processor(mode, api_service)
                            input_list = st.session_state["input_images"]
                            
                            try:
                                result_code = processor.process(
                                    input_data=input_list,
                                    model=selected_model,
                                    extra_prompt=extra_prompt
                                )
                            except TypeError:
                                first_item = input_list[0]
                                result_code = processor.process(
                                    file_bytes=first_item["bytes"],
                                    mime_type=first_item["mime"],
                                    model=selected_model,
                                    extra_prompt=extra_prompt
                                )

                            st.session_state["result"] = result_code
                            st.toast("Xử lý thành công!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi xử lý: {e}", icon=":material/error:")

        # CỘT 2: OUTPUT LATEX CODE
        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
