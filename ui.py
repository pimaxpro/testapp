# ui.py
import streamlit as st
from gemini_service import GeminiAPIService
from config import DEFAULT_EXTRA_PROMPT

class AuthSystem:
    # Danh sách tài khoản & mật khẩu
    USERS = {
        "admin": "123456",
        "thayduong": "math2026",
        "teacher": "latex123"
    }

    @classmethod
    def check_auth(cls):
        """Kiểm tra xem người dùng đã đăng nhập chưa"""
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False

        if not st.session_state["authenticated"]:
            st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>🔒 Đăng nhập hệ thống Math OCR Studio</h2>", unsafe_allow_html=True)
            st.write("")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("login_form"):
                    username = st.text_input("Tên đăng nhập")
                    password = st.text_input("Mật khẩu", type="password")
                    btn_login = st.form_submit_button("Đăng nhập 🚀", use_container_width=True)

                    if btn_login:
                        if username in cls.USERS and cls.USERS[username] == password:
                            st.session_state["authenticated"] = True
                            st.session_state["user_display"] = username
                            st.toast(f"Xin chào {username}!", icon="👋")
                            st.rerun()
                        else:
                            st.error("Tên đăng nhập hoặc mật khẩu không chính xác!")
            return False
        return True


class UIComponent:
    # --- KHU VỰC LƯU TRỮ API KEY DÙNG CHUNG (THẦY CẬP NHẬT TẠI ĐÂY) ---
    SYSTEM_API_KEYS = {
        "Key Hệ Thống 1 (Chính)": "AQ.Ab8RN6LCTf6mo4nUUrCqAqlDYI8B6oFAGQGu7YzIjGcDiRBKeA",
        "Key Hệ Thống 2 (Dự phòng 1)": "AQ.Ab8RN6L3v5pf216_mHlBksO3Py44wnlxmicDCzTS99Th-pao1w",
        "Key Hệ Thống 3 (Dự phòng 2)": "AQ.Ab8RN6K1eOQa7aiXkYNdPtpKcnDSXLw7zTK7SrUvw01Cdf1-gw"
    }

    @staticmethod
    def render_header():
        st.markdown("<h1 class='header-title'>Math OCR Pro Studio</h1>", unsafe_allow_html=True)
        st.markdown("Tổ toán cấp 3 Minh Hoàng")
        st.write("")

    @staticmethod
    def render_sidebar(api_service: GeminiAPIService):
        with st.sidebar:
            st.markdown("## :material/settings: Cấu hình & Chức năng")
            st.markdown("---")
            
            st.markdown("### 🔑 Cấu hình Gemini API Key")
            
            # Tùy chọn nguồn API Key
            key_source = st.radio(
                "Nguồn API Key:",
                options=["Dùng Key mặc định (Kho hệ thống)", "Nhập Key cá nhân"],
                index=0,
                horizontal=False
            )

            active_api_key = ""

            if key_source == "Dùng Key mặc định (Kho hệ thống)":
                # Lựa chọn 1 trong các Key có sẵn trong kho
                selected_key_label = st.selectbox(
                    "Chọn Key hệ thống khả dụng:",
                    options=list(UIComponent.SYSTEM_API_KEYS.keys())
                )
                active_api_key = UIComponent.SYSTEM_API_KEYS.get(selected_key_label, "")
                st.caption("🟢 *Đang sử dụng API Key do hệ thống cung cấp.*")

            else:
                # Nhập Key cá nhân
                saved_key = st.session_state.get("api_key_custom", "")
                active_api_key = st.text_input(
                    "Nhập Gemini API Key của bạn:", 
                    value=saved_key, 
                    type="password",
                    help="Key của bạn sẽ được ưu tiên sử dụng riêng."
                )
                st.session_state["api_key_custom"] = active_api_key
                if active_api_key:
                    st.caption(":material/check_circle: *Đã ghi nhận Key cá nhân.*")

            # Cập nhật Key vào Session State chung
            st.session_state["api_key"] = active_api_key

            st.markdown("---")

            # Danh sách 3 chức năng chính
            mode = st.selectbox(
                "Chọn Chức năng Processing",
                options=["latex", "ex_test", "tikz"],
                format_func=lambda x: {
                    "latex": "📄 1. Chuyển file sang Latex",
                    "ex_test": "📝 2. Chuyển bài toán sang ex_test",
                    "tikz": "🎨 3. Chuyển ảnh sang tikz"
                }[x]
            )

            # Tùy chọn lời giải cho ex_test
            add_solution = False
            if mode == "ex_test":
                solution_option = st.radio(
                    "Tùy chọn lời giải:",
                    options=["Giữ nguyên gốc", "Thêm lời giải (Tự động giải)"],
                    index=0,
                    help="Chọn tự động giải chi tiết hoặc giữ nguyên khung lời giải như đề gốc."
                )
                add_solution = (solution_option == "Thêm lời giải (Tự động giải)")

            st.markdown("---")

            available_models = api_service.get_available_models() if active_api_key else ["Vui lòng chọn/nhập API Key"]
            model_choice = st.selectbox("Mô hình Gemini Vision", available_models, index=0)

            return active_api_key, mode, model_choice, add_solution

    @staticmethod
    def render_input_section():
        """Khu vực Upload, Paste Clipboard, Preview và Yêu cầu bổ sung"""
        st.markdown("### 1. Dữ liệu đầu vào")

        if "input_images" not in st.session_state:
            st.session_state["input_images"] = []

        col_up, col_paste = st.columns([7, 3])
        with col_up:
            uploaded_files = st.file_uploader(
                "Tải lên hoặc Kéo thả Ảnh / PDF", 
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                accept_multiple_files=True,
                label_visibility="collapsed"
            )
        with col_paste:
            btn_paste = st.button("📋 Dán từ Clipboard", use_container_width=True)

        if st.session_state["input_images"]:
            st.caption(f"📸 Đã nhận **{len(st.session_state['input_images'])}** tệp đầu vào:")
            cols = st.columns(min(len(st.session_state["input_images"]), 4))
            for idx, img in enumerate(st.session_state["input_images"]):
                with cols[idx % 4]:
                    st.image(img, use_container_width=True, caption=f"Ảnh {idx + 1}")

        st.markdown("---")

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

        return btn_process, extra_notes, uploaded_files, btn_paste

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
