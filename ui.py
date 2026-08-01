# ui.py
import streamlit as st
from gemini_service import GeminiAPIService
from config import DEFAULT_EXTRA_PROMPT

class UIComponent:
    @staticmethod
    def render_header():
        st.markdown("<h1 class='header-title'>Math OCR Pro Studio</h1>", unsafe_allow_html=True)
        st.markdown("Hệ thống chuyển đổi **Ảnh / PDF / Clipboard** thành mã **ex_test**, **TikZ**, và **Tự động soạn Lời giải**.")
        st.write("")

    @staticmethod
    def render_sidebar(api_service: GeminiAPIService):
        with st.sidebar:
            st.markdown("## :material/settings: Cấu hình & Chức năng")
            st.markdown("---")
            
            saved_key = st.session_state.get("api_key", "")
            if not saved_key:
                query_params = st.query_params
                saved_key = query_params.get("api_key", "")
                if saved_key:
                    st.session_state["api_key"] = saved_key

            api_key_input = st.text_input(
                "Gemini API Key", 
                value=saved_key, 
                type="password",
                help="Key sẽ được tự động ghi nhớ cho các lần truy cập sau trên trình duyệt này."
            )
            
            if api_key_input != st.session_state.get("api_key", ""):
                st.session_state["api_key"] = api_key_input
                st.query_params["api_key"] = api_key_input
                st.rerun()

            if api_key_input:
                st.caption(":material/check_circle: *Đã lưu API Key cho phiên làm việc này*")

            st.markdown("---")

            mode = st.selectbox(
                "Chọn Chức năng Processing",
                options=["ex_test", "ex_test_solve", "tikz"],
                format_func=lambda x: {
                    "ex_test": "📄 OCR sang gói ex_test (Đề thi)",
                    "ex_test_solve": "🧠 ex_test + Tự soạn Lời giải",
                    "tikz": "🎨 Chuyển Hình vẽ -> Mã TikZ"
                }[x]
            )

            available_models = api_service.get_available_models() if api_key_input else ["Vui lòng nhập API Key"]
            model_choice = st.selectbox("Mô hình Gemini Vision", available_models, index=0)

            return api_key_input, mode, model_choice

    @staticmethod
    def render_input_section():
        """Khu vực Upload, Preview nhiều ảnh và Yêu cầu bổ sung"""
        st.markdown("### 1. Dữ liệu đầu vào")

        # Box tải lên nhiều file (Ảnh / PDF)
        uploaded_files = st.file_uploader(
            "Tải lên hoặc Kéo thả nhiều Ảnh / PDF", 
            type=["png", "jpg", "jpeg", "webp", "pdf"],
            accept_multiple_files=True
        )

        # Cấu trúc lưu trữ danh sách ảnh trong Session State
        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []

        # Cập nhật danh sách từ uploader
        if uploaded_files:
            st.session_state["input_images"] = uploaded_files

        # Hiển thị danh sách / Preview các ảnh đã upload/dán
        if st.session_state["input_images"]:
            st.caption(f"📸 Đã nhận **{len(st.session_state['input_images'])}** tệp đầu vào:")
            cols = st.columns(min(len(st.session_state["input_images"]), 4))
            for idx, img in enumerate(st.session_state["input_images"]):
                with cols[idx % 4]:
                    st.image(img, use_container_width=True, caption=f"Ảnh {idx + 1}")

        st.markdown("---")

        # Box Yêu cầu bổ sung cho AI (đã chuyển từ Sidebar sang)
        if "extra_notes_val" not in st.session_state:
            st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

        extra_notes = st.text_area(
            "💡 Yêu cầu bổ sung cho AI", 
            value=st.session_state["extra_notes_val"],
            height=120,
            help="Nhập các quy tắc định dạng riêng hoặc lưu ý cho bài toán tại đây."
        )
        st.session_state["extra_notes_val"] = extra_notes

        st.markdown("---")

        # 2 nút bấm đặt cùng hàng, kích thước bằng nhau
        col1, col2 = st.columns(2)
        with col1:
            btn_process = st.button(
                "🚀 Trích xuất LaTeX", 
                type="primary", 
                use_container_width=True
            )
        with col2:
            btn_clear = st.button(
                "🗑️ Xóa danh sách ảnh", 
                type="secondary", 
                use_container_width=True
            )

        if btn_clear:
            st.session_state["input_images"] = []
            st.rerun()

        return btn_process, extra_notes

    @staticmethod
    def render_output_section():
        """Hiển thị box st.code chuẩn native đẹp mắt"""
        st.markdown("### 2. Mã LaTeX Trích Xuất")
        
        if "result" in st.session_state and st.session_state["result"]:
            latex_code = st.session_state["result"]
            
            if "\\begin{tkz" in latex_code or "\\begin{tikzpicture}" in latex_code:
                st.warning("Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)", icon=":material/draw:")
            
            st.code(latex_code, language="latex", line_numbers=True)

        else:
            UIComponent.render_empty_state()

    @staticmethod
    def render_empty_state():
        st.info("Chưa có kết quả. Vui lòng tải/dán ảnh và bấm nút trích xuất.", icon=":material/info:")
