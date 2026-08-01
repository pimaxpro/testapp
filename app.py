import io
import streamlit as st
from PIL import Image
from config import CUSTOM_CSS, DEFAULT_EXTRA_PROMPT
from gemini_service import GeminiAPIService
from processors import ProcessorFactory
from ui import UIComponent

st.set_page_config(
    page_title="Math OCR Pro - Studio", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STYLING GIAO DIỆN STUDIO ====================
STUDIO_DESIGN_CSS = CUSTOM_CSS + """
<style>
    :root {
        --primary-color: #4F46E5 !important;
        --primary-hover: #4338CA !important;
        --bg-card: #181825 !important;
        --border-color: #313244 !important;
        --text-muted: #A6ADC8 !important;
    }

    /* Triệt tiêu viền đỏ mặc định của Streamlit khi focus */
    div[data-baseweb="textarea"]:focus-within,
    div[data-baseweb="input"]:focus-within {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
    }

    /* Cấu hình khung Box Editor */
    .stTextArea textarea {
        background-color: var(--bg-card) !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: #CDD6F4 !important;
        font-size: 14px !important;
        transition: border-color 0.2s ease;
    }
    .stTextArea textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
    }

    /* Đồng bộ nút bấm chân trang */
    .stButton button {
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stButton button[kind="primary"] {
        background-color: var(--primary-color) !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25) !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: var(--primary-hover) !important;
    }
    .stButton button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        color: var(--text-muted) !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: #EF4444 !important;
        color: #EF4444 !important;
    }
</style>
"""
st.markdown(STUDIO_DESIGN_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def __init__(self):
        pass

    def run(self):
        # 1. Khởi tạo State ban đầu
        if "api_key" not in st.session_state:
            st.session_state["api_key"] = st.query_params.get("api_key", "")
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []
        if "uploader_key" not in st.session_state:
            st.session_state["uploader_key"] = 0

        UIComponent.render_header()
        
        current_key = st.session_state.get("api_key", "")
        api_service = GeminiAPIService(api_key=current_key)
        
        # 2. Render Sidebar
        api_key, mode, selected_model = UIComponent.render_sidebar(api_service)
        
        api_service.api_key = api_key
        if api_key and not getattr(api_service, 'client', None):
            api_service.client = GeminiAPIService(api_key).client

        col1, col2 = st.columns([5, 7], gap="large")

        # ==================== CỘT 1: INPUT & CONTROLS ====================
        with col1:
            st.markdown("### 📥 Nội dung & Yêu cầu")
            
            # --- BOX 1: EDITOR NHẬP VĂN BẢN/BÀI TOÁN CHÍNH ---
            main_text = st.text_area(
                "Nội dung bài toán",
                height=180,
                placeholder="Nhập hoặc dán nội dung bài toán vào đây...",
                label_visibility="collapsed"
            )

            # --- KHUNG HIỂN THỊ FILE ĐÃ TẢI KÈM NÚT XÓA TỪNG FILE ---
            if st.session_state.get("input_images"):
                st.caption("📷 Danh sách file/ảnh đã đính kèm:")
                num_files = len(st.session_state["input_images"])
                cols = st.columns(min(num_files, 4))
                
                # Duyệt danh sách an toàn để hỗ trợ xóa
                for idx, item in enumerate(list(st.session_state["input_images"])):
                    with cols[idx % 4]:
                        with st.container(border=True):
                            if item["mime"] == "application/pdf":
                                st.write(f"📄 `{item['name'][:8]}`")
                            elif item.get("preview"):
                                st.image(item["preview"], use_container_width=True)
                            
                            # Nút xóa đơn lẻ từng file
                            if st.button("✖ Xóa", key=f"del_{idx}", use_container_width=True):
                                st.session_state["input_images"].pop(idx)
                                st.rerun()

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # --- BOX 2: GHI CHÚ BỔ SUNG CHO AI ---
            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_prompt = st.text_area(
                "Yêu cầu bổ sung cho AI",
                value=st.session_state["extra_notes_val"],
                height=90,
                placeholder="Nhập yêu cầu bổ sung cho AI (ví dụ: Chuyển sang mã TikZ, vẽ lại hình...)...",
                label_visibility="collapsed"
            )
            st.session_state["extra_notes_val"] = extra_prompt

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

            # --- HÀNG CÁC NÚT THAO TÁC CĂN ĐỀU BÊN DƯỚI ---
            act_col1, act_col2, act_col3 = st.columns([4, 3, 3])
            
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

            # --- XỬ LÝ TẢI FILE NÂNG CAO (CHỐNG NHÁY/LẶP VO HẠN) ---
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

                # Chỉ làm mới key uploader và rerun khi thực sự nhận thêm file mới
                if has_new_file:
                    st.session_state["uploader_key"] += 1
                    st.rerun()

            # --- SỰ KIỆN NÚT BẤM ---
            if btn_clear_all:
                st.session_state["input_images"] = []
                st.rerun()

            if btn_process:
                if not api_key:
                    st.error("Vui lòng nhập API Key ở thanh bên!", icon="🔑")
                elif not st.session_state.get("input_images") and not main_text.strip():
                    st.error("Vui lòng nhập văn bản hoặc tải file lên!", icon="⚠️")
                else:
                    with st.spinner("Đang xử lý toán học..."):
                        try:
                            combined_prompt = ""
                            if main_text.strip():
                                combined_prompt += f"Văn bản đầu vào:\n{main_text}\n\n"
                            if extra_prompt.strip():
                                combined_prompt += f"Ghi chú bổ sung:\n{extra_prompt}"

                            processor = ProcessorFactory.get_processor(mode, api_service)
                            input_list = st.session_state.get("input_images", [])
                            
                            try:
                                result_code = processor.process(
                                    input_data=input_list,
                                    model=selected_model,
                                    extra_prompt=combined_prompt
                                )
                            except TypeError:
                                first_item = input_list[0] if input_list else {"bytes": None, "mime": None}
                                result_code = processor.process(
                                    file_bytes=first_item.get("bytes"),
                                    mime_type=first_item.get("mime"),
                                    model=selected_model,
                                    extra_prompt=combined_prompt
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
