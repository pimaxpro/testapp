import streamlit as st
from gemini_service import GeminiAPIService
from streamlit_paste_button import paste_image_button

class UIComponent:
    @staticmethod
    def render_header():
        st.markdown("<h1 class='header-title'>Math OCR Pro Studio</h1>", unsafe_allow_html=True)
        st.markdown("Hệ thống chuyển đổi Ảnh/PDF/Clipboard thành **ex_test**, **TikZ**, và **Tự động soạn Lời giải**.")
        st.write("")

    @staticmethod
    def render_sidebar(api_service: GeminiAPIService):
        with st.sidebar:
            st.markdown("## Cấu hình & Mode")
            st.markdown("---")
            
            # --- TỰ ĐỘNG KHÔI PHỤC API KEY DÃ LƯU ---
            # 1. Ưu tiên lấy từ session_state
            # 2. Nếu chưa có, kiểm tra URL query params
            saved_key = st.session_state.get("api_key", "")
            if not saved_key:
                query_params = st.query_params
                saved_key = query_params.get("api_key", "")
                if saved_key:
                    st.session_state["api_key"] = saved_key

            # Ô nhập API Key
            api_key_input = st.text_input(
                "Gemini API Key", 
                value=saved_key, 
                type="password",
                help="Key sẽ được tự động ghi nhớ cho các lần truy cập sau trên trình duyệt này."
            )
            
            # Nếu người dùng thay đổi/nhập key mới -> Cập nhật lưu lại ngay
            if api_key_input != st.session_state.get("api_key", ""):
                st.session_state["api_key"] = api_key_input
                st.query_params["api_key"] = api_key_input  # Lưu vào URL param để giữ khi F5
                st.rerun()

            # Hiển thị trạng thái đã lưu Key
            if api_key_input:
                st.caption("✅ *Đã lưu API Key cho phiên làm việc này*")

            st.markdown("---")

            mode = st.selectbox(
                "Chọn Chức năng Processing",
                options=["ex_test", "ex_test_solve", "tikz"],
                format_func=lambda x: {
                    "ex_test": "OCR sang gói ex_test (Đề thi)",
                    "ex_test_solve": "ex_test + Tự soạn Lời giải",
                    "tikz": "Chuyển Hình vẽ -> Mã TikZ"
                }[x]
            )

            available_models = api_service.get_available_models() if api_key_input else ["Vui lòng nhập API Key"]
            model_choice = st.selectbox("Mô hình Gemini Vision", available_models, index=0)

            st.markdown("---")
            extra_notes = st.text_area("Ghi chú/Yêu cầu bổ sung", placeholder="VD: Đánh số câu từ Câu 5...", height=100)

            return api_key_input, mode, model_choice, extra_notes

    @staticmethod
    def render_empty_state():
        st.markdown(
            """
            <div style="border: 2px dashed rgba(128, 128, 128, 0.3); border-radius: 12px; padding: 60px 20px; text-align: center; color: #888888; margin-top: 10px;">
                <p style="font-size: 32px; margin-bottom: 5px;">🧩</p>
                <p style="font-weight: 500;">Mã LaTeX xuất ra sẽ hiển thị ở đây.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
