import streamlit as st
from gemini_service import get_available_models

def render_sidebar():
    """Vẽ Sidebar cấu hình"""
    with st.sidebar:
        st.markdown("## ⚙️ **Cấu hình Hệ thống**")
        st.markdown("---")
        
        api_key = st.text_input("Gemini API Key", type="password", placeholder="AIzaSy...")
        
        if api_key:
            available_models = get_available_models(api_key)
        else:
            available_models = ["Vui lòng nhập API Key trước"]
            
        model_choice = st.selectbox(
            "Mô hình Gemini Vision", 
            available_models,
            index=0,
            help="Danh sách mô hình đọc ảnh khả dụng trên tài khoản của bạn."
        )
        
        st.markdown("---")
        extra_notes = st.text_area(
            "📝 **Ghi chú/Yêu cầu bổ sung**", 
            placeholder="VD: Dùng tkz-tab cho BBT, dùng align* cho hệ phương trình...",
            height=120
        )
        st.caption("✨ Tự động tối ưu mã cho Overleaf, LaTeX Studio và các trình biên soạn chuyên nghiệp.")
        
        return api_key, model_choice, extra_notes

def render_header():
    """Vẽ Tiêu đề ứng dụng"""
    st.markdown("<h1 class='header-title'>🧮 Math OCR Studio Pro</h1>", unsafe_allow_html=True)
    st.markdown("Chuyển đổi hình ảnh bài toán, công thức, đồ thị & bảng biến thiên thành **mã LaTeX chuẩn**.")
    st.write("")

def render_empty_state():
    """Vẽ khung chờ ở Cột 2 khi chưa có kết quả"""
    st.markdown(
        """
        <div style="
            border: 2px dashed rgba(128, 128, 128, 0.3); 
            border-radius: 12px; 
            padding: 60px 20px; 
            text-align: center;
            color: #888888;
            margin-top: 10px;">
            <p style="font-size: 40px; margin-bottom: 10px;">💻</p>
            <p style="font-weight: 500;">Mã LaTeX sẽ xuất hiện ở đây sau khi bạn bấm "Trích xuất Mã LaTeX".</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
