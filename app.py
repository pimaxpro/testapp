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

# Inject CSS tùy chỉnh để làm đẹp đồng bộ 2 nút Input & Bảng màu
CUSTOM_UI_STYLING = CUSTOM_CSS + """
<style>
    /* Đồng bộ tông màu chủ đạo */
    :root {
        --primary-color: #4F46E5;
        --primary-hover: #4338CA;
        --bg-card: #1E1E2E;
    }
    
    /* Cấu trúc Nút dán từ Clipboard */
    div[data-testid="stCustomComponentV1"] iframe {
        height: 52px !important;
    }
    
    /* Thiết kế Custom File Uploader dạng Nút bấm vuông vắn khớp với Paste Button */
    div[data-testid="stFileUploader"] {
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 6px 12px !important;
        background-color: #262636 !important;
        border: 1px dashed #4F46E5 !important;
        border-radius: 8px !important;
        height: 52px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stFileUploader"] section small {
        display: none !important; /* Ẩn bớt text dung lượng thừa */
    }
    
    /* Bo góc và tùy chỉnh khung preview ảnh */
    .media-card {
        background-color: #181825;
        border: 1px solid #313244;
        border-radius: 8px;
        padding: 8px;
        text-align: center;
    }
</style>
"""
st.markdown(CUSTOM_UI_STYLING, unsafe_allow_html=True)

class MathOCRApp:
    """Controller chính điều phối toàn bộ ứng dụng"""
    def __init__(self):
        pass

    def run(self):
        # KHỞI TẠO SESSION STATE
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

        # CỘT 1: INPUT COMPONENT
        with col1:
            st.markdown("### 📥 Dữ liệu đầu vào")
            
            # --- KHU VỰC 2 NÚT SONG SONG CÙNG KÍCH THƯỚC ---
            in_col1, in_col2 = st.columns(2, gap="small")

            with in_col1:
                paste_result = paste_image_button(
                    label="📋 Dán từ Clipboard",
                    background_color="#4F46E5",
                    text_color="#FFFFFF",
                    hover_background_color="#4338CA",
                )

            with in_col2:
                uploaded_files = st.file_uploader(
                    "Tải tệp Ảnh / PDF", 
                    type=["png", "jpg", "jpeg", "webp", "pdf"],
                    accept_multiple_files=True,
                    label_visibility="collapsed"
                )

            # Xử lý logic Clipboard
            if paste_result.image_data is not None:
                image = paste_result.image_data
                buf = io.BytesIO()
                image.save(buf, format="PNG")
                img_bytes = buf.getvalue()
                
                if "last_pasted" not in st.session_state or st.session_state["last_pasted"] != img_bytes:
                    st.session_state["last_pasted"] = img_bytes
                    st.session_state["input_images"].append({
                        "name": f"Clipboard_{len(st.session_state['input_images']) + 1}.png",
                        "bytes": img_bytes,
                        "mime": "image/png",
                        "preview": image
                    })
                    st.toast("Đã dán ảnh thành công!", icon="📋")

            # Xử lý logic File Uploader
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

            # --- KHU VỰC PREVIEW TỆP ĐÃ TẢI LÊN ---
            if st.session_state.get("input_images"):
                st.caption(f"Đã chọn **{len(st.session_state['input_images'])}** tệp:")
                cols = st.columns(min(len(st.session_state["input_images"]), 4))
                for idx, item in enumerate(st.session_state["input_images"]):
                    with cols[idx % 4]:
                        if item["mime"] == "application/pdf":
                            st.info(f"📄 {item['name'][:10]}...", icon=":material/description:")
                        elif item.get("preview"):
                            st.image(item["preview"], use_container_width=True)

            # --- KHU VỰC NHẬP PROMPT BỔ SUNG ---
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "💡 Yêu cầu bổ sung cho AI", 
                value=st.session_state["extra_notes_val"],
                height=100,
                placeholder="Nhập ghi chú định dạng thêm nếu có..."
            )
            st.session_state["extra_notes_val"] = extra_prompt

            # --- KHU VỰC THAO TÁC (TRÍCH XUẤT / XÓA) ---
            btn_col1, btn_col2 = st.columns([2, 1], gap="small")
            with btn_col1:
                btn_process = st.button(
                    "🚀 Trích xuất & Chuyển đổi", 
                    type="primary", 
                    use_container_width=True
                )
            with btn_col2:
                btn_clear = st.button(
                    "🗑️ Xóa tất cả", 
                    type="secondary", 
                    use_container_width=True
                )

            # SỰ KIỆN NÚT BẤM
            if btn_clear:
                st.session_state["input_images"] = []
                if "last_pasted" in st.session_state:
                    del st.session_state["last_pasted"]
                st.rerun()

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên trái!", icon="🔑")
                elif not st.session_state.get("input_images"):
                    st.error("Chưa có ảnh/PDF nào được chọn!", icon="🖼️")
                else:
                    with st.spinner("Đang xử lý toán học..."):
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
                            st.toast("Trích xuất hoàn tất!", icon="✅")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi hệ thống: {e}", icon="❌")

        # CỘT 2: OUTPUT LATEX CODE
        with col2:
            UIComponent.render_output_section()

if __name__ == "__main__":
    app = MathOCRApp()
    app.run()
