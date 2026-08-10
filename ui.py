# ui.py
import streamlit as st
from gemini_service import GeminiAPIService
from config import DEFAULT_EXTRA_PROMPT

class AuthSystem:
    # Danh sách tài khoản & mật khẩu
    USERS = {
        "0839032003": "2003",
        "0343763310": "3310",
        "0943170177": "0177",
        "0934682505": "2505",
        "0388262917": "2917"
    }

    @classmethod
    def check_auth(cls):
        """Kiểm tra xem người dùng đã đăng nhập chưa"""
        if "authenticated" not in st.session_state:
            st.session_state["authenticated"] = False

        if not st.session_state["authenticated"]:
            st.markdown("<h2 style='text-align: center; margin-top: 2rem;'>Liên hệ bé Tuấn để có tài khoản nhé!</h2>", unsafe_allow_html=True)
            st.write("")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                with st.form("login_form"):
                    username = st.text_input("Tên đăng nhập")
                    password = st.text_input("Mật khẩu", type="password")
                    btn_login = st.form_submit_button("Đăng nhập", use_container_width=True)

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
    @staticmethod
    def render_header():
        st.markdown("<h1 class='header-title'>Tổ toán cấp 3 Minh Hoàng</h1>", unsafe_allow_html=True)
        st.markdown("Quý nào cũng đạt KPI nhé!")
        st.write("")

    @staticmethod
    def render_sidebar(api_service: GeminiAPIService):
        with st.sidebar:
            st.markdown("## ⚙️ Cấu hình & Chức năng")
            
            # --- Nhóm 1: Cấu hình API Key (Đã làm lại UI) ---
            st.markdown("##### 🔑 Cấu hình Gemini API Key")
            
            # Thêm dòng chú thích mờ nhỏ gọn, thanh lịch
            st.markdown("<p style='font-size: 0.85em; color: #555; margin-bottom: 5px;'>Nhập API Key cá nhân của bạn để sử dụng AI (bắt đầu bằng AIzaSy...)</p>", unsafe_allow_html=True)

            saved_key = st.session_state.get("api_key_custom", "")
            active_api_key = st.text_input(
                "Nhập Gemini API Key cá nhân:", 
                value=saved_key, 
                type="password",
                placeholder="AIzaSy...",
                label_visibility="collapsed"
            )
            st.session_state["api_key_custom"] = active_api_key
            
            # Hiển thị trạng thái bằng UI Box đẹp mắt thay vì text caption
            if active_api_key:
                st.success("Đã ghi nhận API Key", icon="✅")
            else:
                st.info("Vui lòng nhập API Key để tiếp tục", icon="ℹ️")

            st.markdown("---") # Đường kẻ mờ ngăn cách cho sidebar thoáng hơn

            # Cập nhật Key vào Session State và gán trực tiếp cho service
            st.session_state["api_key"] = active_api_key
            api_service.api_key = active_api_key

            # --- Nhóm 2: Chức năng Processing ---
            st.markdown("##### 📝 Chức năng Processing")
            mode = st.selectbox(
                "Chọn Chức năng Processing",
                options=["latex", "ex_test", "tikz"],
                format_func=lambda x: {
                    "latex": "📄 1. Chuyển file sang Latex",
                    "ex_test": "📝 2. Chuyển bài toán sang ex_test",
                    "tikz": "🎨 3. Chuyển ảnh sang tikz"
                }[x],
                label_visibility="collapsed"
            )

            add_solution = False
            if mode == "ex_test":
                solution_option = st.radio(
                    "Tùy chọn lời giải:",
                    options=["Giữ nguyên gốc", "Thêm lời giải (Tự động giải)"],
                    index=0,
                    horizontal=True
                )
                add_solution = (solution_option == "Thêm lời giải (Tự động giải)")

            # --- Nhóm 3: Mô hình AI ---
            st.markdown("##### 🤖 Mô hình Gemini Vision")
            available_models = api_service.get_available_models()
            model_choice = st.selectbox(
                "Mô hình Gemini Vision", 
                available_models, 
                index=0,
                label_visibility="collapsed"
            )

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
                st.warning("Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)", icon="🎨")
            
            st.code(latex_code, language="latex", line_numbers=True)

        else:
            UIComponent.render_empty_state()

    @staticmethod
    def render_empty_state():
        st.info("Chưa có kết quả. Vui lòng tải/dán ảnh và bấm nút trích xuất.", icon="ℹ️")
