import streamlit as st
from gemini_service import GeminiAPIService

class UIComponent:
    @staticmethod
    def render_header():
        st.markdown("<h1 class='header-title'>🧮 Math OCR Pro - OOP Studio</h1>", unsafe_allow_html=True)
        st.markdown("Hệ thống chuyển đổi Ảnh/PDF thành **ex_test**, **TikZ**, và **Tự động soạn Lời giải**.")
        st.write("")

    @staticmethod
    def render_sidebar(api_service: GeminiAPIService):
        with st.sidebar:
            st.markdown("## ⚙️ **Cấu hình & Mode**")
            st.markdown("---")
            
            api_key = st.text_input("Gemini API Key", value=api_service.api_key, type="password")
            
            # Chọn chế độ chức năng
            mode = st.selectbox(
                "🎯 **Chọn Chức năng Processing**",
                options=["ex_test", "ex_test_solve", "tikz"],
                format_func=lambda x: {
                    "ex_test": "📄 OCR sang gói ex_test (Đề thi)",
                    "ex_test_solve": "🧠 ex_test + Tự soạn Lời giải",
                    "tikz": "🎨 Chuyển Hình vẽ -> Mã TikZ"
                }[x]
            )

            available_models = api_service.get_available_models() if api_key else ["Vui lòng nhập API Key"]
            model_choice = st.selectbox("Mô hình Gemini Vision", available_models, index=0)

            st.markdown("---")
            extra_notes = st.text_area("📝 **Ghi chú/Yêu cầu bổ sung**", placeholder="VD: Đánh số câu từ Câu 5...", height=100)

            return api_key, mode, model_choice, extra_notes

    @staticmethod
    def render_empty_state():
        st.markdown(
            """
            <div style="border: 2px dashed rgba(128, 128, 128, 0.3); border-radius: 12px; padding: 60px 20px; text-align: center; color: #888888; margin-top: 10px;">
                <p style="font-size: 40px; margin-bottom: 10px;">💻</p>
                <p style="font-weight: 500;">Mã LaTeX xuất ra sẽ hiển thị ở đây.</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
