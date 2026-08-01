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

            st.markdown("---")

            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_notes = st.text_area(
                "Ghi chú / Yêu cầu định dạng AI", 
                value=st.session_state["extra_notes_val"],
                height=130
            )
            st.session_state["extra_notes_val"] = extra_notes

            return api_key_input, mode, model_choice, extra_notes

    @staticmethod
    def render_output_section():
        """Khu vực Output: Đúng 1 box duy nhất vừa hiển thị vừa chỉnh sửa"""
        st.markdown("### 2. Mã LaTeX Trích Xuất")
        
        if "result" in st.session_state and st.session_state["result"]:
            latex_code = st.session_state["result"]
            
            if "\\begin{tkz" in latex_code or "\\begin{tikzpicture}" in latex_code:
                st.warning("Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)", icon=":material/draw:")
            
            # ĐÂY LÀ BOX DUY NHẤT: Vừa đẹp như code box vừa gõ/chỉnh sửa trực tiếp được
            edited_code = st.text_area(
                "LaTeX Code Editor", 
                value=latex_code, 
                height=520, 
                label_visibility="collapsed"
            )
            
            if edited_code != latex_code:
                st.session_state["result"] = edited_code
        else:
            UIComponent.render_empty_state()

    @staticmethod
    def render_empty_state():
        st.info("Chưa có kết quả. Vui lòng tải/dán ảnh và bấm nút trích xuất.", icon=":material/info:")
