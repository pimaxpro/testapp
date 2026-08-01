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

# ==================== STYLING GIAO DIỆN TĨNH HOÀN TOÀN (ZERO FOCUS EFFECT) ====================
STUDIO_DESIGN_CSS = CUSTOM_CSS + """
<style>
    :root {
        --primary-color: #4F46E5 !important;
        --primary-hover: #4338CA !important;
        --bg-edit-box: #FFFFFF !important;
        --border-color: #CBD5E1 !important;
        --text-color: #0F172A !important;
    }

    /* 1. TRIỆT TIÊU TOÀN BỘ HIỆU ỨNG FOCUS/ACTIVE TRÊN TOÀN BỘ WEB */
    *, *:focus, *:focus-within, *:active, *:hover {
        outline: none !important;
        box-shadow: none !important;
    }

    /* 2. ÉP THẺ BỌC NGOÀI CỦA BASEWEB TĨNH HOÀN TOÀN */
    div[data-baseweb="textarea"],
    div[data-baseweb="base-input"],
    div[data-baseweb="input"] {
        background-color: var(--bg-edit-box) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Giữ nguyên trạng thái khi click vào (không đổi màu, không đổi viền) */
    div[data-baseweb="textarea"]:focus-within,
    div[data-baseweb="base-input"]:focus-within,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="textarea"]:hover,
    div[data-baseweb="base-input"]:hover {
        border-color: var(--border-color) !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* 3. THẺ TEXTAREA BÊN TRONG CŨNG TĨNH HOÀN TOÀN */
    .stTextArea textarea {
        background-color: transparent !important;
        border: none !important;
        border-radius: 8px !important;
        color: var(--text-color) !important;
        font-size: 14px !important;
        font-weight: 450 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    .stTextArea textarea:focus, 
    .stTextArea textarea:active {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Màu chữ gợi ý (placeholder) */
    .stTextArea textarea::placeholder {
        color: #94A3B8 !important;
    }

    /* 4. NÚT BẤM PHẲNG TĨNH */
    .stButton button {
        height: 42px !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        box-shadow: none !important;
        outline: none !important;
    }
    .stButton button[kind="primary"] {
        background-color: var(--primary-color) !important;
        border: none !important;
        color: #FFFFFF !important;
    }
    .stButton button[kind="primary"]:hover {
        background-color: var(--primary-hover) !important;
        box-shadow: none !important;
    }
    .stButton button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid var(--border-color) !important;
        color: #64748B !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: #EF4444 !important;
        color: #EF4444 !important;
        box-shadow: none !important;
    }
</style>
"""
st.markdown(STUDIO_DESIGN_CSS, unsafe_allow_html=True)

class MathOCRApp:
    def __init__(self):
        pass

    def run(self):
        # 1. Khởi tạo Session State ban đầu
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
                
                # Duyệt danh sách file bằng bản sao list để xóa an toàn
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

            # --- XỬ LÝ TẢI FILE NÂNG CAO (CHỐNG NHÁY/LẶP VÔ HẠN) ---
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

                # Chỉ reset key uploader và rerun khi có file mới
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
                            
                            # Xử lý tương thích linh hoạt tham số gọi Processor
                            try:
                                result_code = processor.process(
                                    input_data=input_list,
                                    model=selected_model,
                                    extra_prompt=combined_prompt
                                )
                            except TypeError:
                                try:
                                    result_code = processor.process(
                                        image_input=input_list,
                                        model_name=selected_model,
                                        system_instruction="",
                                        extra_notes=combined_prompt
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
