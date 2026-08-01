import streamlit as st
from code_editor import code_editor
from gemini_service import GeminiAPIService
from config import DEFAULT_EXTRA_PROMPT

class UIComponent:
    # ... (Các hàm render_header và render_sidebar giữ nguyên) ...

    @staticmethod
    def render_output_section():
        """Box code giữ nguyên thiết kế đẹp, có Syntax Highlighting và CHO PHÉP SỬA TRỰC TIẾP"""
        st.markdown("### 2. Mã LaTeX Trích Xuất")
        
        if "result" in st.session_state and st.session_state["result"]:
            latex_code = st.session_state["result"]
            
            if "\\begin{tkz" in latex_code or "\\begin{tikzpicture}" in latex_code:
                st.warning("Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)", icon=":material/draw:")

            # Cấu hình giao diện chuẩn Overleaf / Dark theme cho Editor
            custom_buttons = [{
                "name": "Copy",
                "feather": "Copy",
                "hasCommand": True,
                "command": "copyToClipboard",
                "style": {"top": "0.5rem", "right": "0.5rem"}
            }]
            
            # Khối hiển thị code duy nhất: Đẹp như st.code() nhưng gõ/sửa trực tiếp được!
            response = code_editor(
                code=latex_code,
                lang="latex",
                theme="monokai", # Giao diện tối mượt mà chuẩn code editor
                height="500px",
                buttons=custom_buttons,
                options={"wrap": True, "fontFamily": "Consolas, monospace", "fontSize": "14px"}
            )
            
            # Cập nhật lại session_state nếu thầy có chỉnh sửa văn bản trong box
            if response['type'] == "submit" or response['text'] != latex_code:
                if response['text']:
                    st.session_state["result"] = response['text']
        else:
            UIComponent.render_empty_state()

    @staticmethod
    def render_empty_state():
        st.info("Chưa có kết quả. Vui lòng tải/dán ảnh và bấm nút trích xuất.", icon=":material/info:")
