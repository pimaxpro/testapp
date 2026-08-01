import streamlit as st
from config import CUSTOM_CSS
from ui import render_sidebar, render_header, render_empty_state
from gemini_service import convert_image_to_latex

# Cấu hình Page
st.set_page_config(
    page_title="Math OCR Pro - Image to LaTeX", 
    page_icon="🧮", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Main Application logic
def main():
    api_key, model_choice, extra_notes = render_sidebar()
    render_header()

    col1, col2 = st.columns([5, 7], gap="large")

    # CỘT 1: INPUT
    with col1:
        st.markdown("### 📸 **1. Tải ảnh đầu vào**")
        uploaded = st.file_uploader(
            "Thả ảnh hoặc bấm để chọn (PNG, JPG, WEBP)", 
            type=["png", "jpg", "jpeg", "webp"],
            label_visibility="collapsed"
        )
        
        if uploaded:
            st.image(uploaded, use_container_width=True)
            if st.button("🚀 Trích xuất Mã LaTeX", type="primary", use_container_width=True):
                if not api_key:
                    st.error("⚠️ Vui lòng nhập API Key ở thanh bên trái!")
                else:
                    with st.spinner("⚡ Đang phân tích cấu trúc toán học..."):
                        try:
                            clean_res = convert_image_to_latex(
                                uploaded.getvalue(), 
                                uploaded.type, 
                                api_key, 
                                model_choice, 
                                extra_notes
                            )
                            st.session_state["result"] = clean_res
                            st.toast("Chuyển đổi thành công!", icon="✅")
                        except Exception as e:
                            st.error(f"❌ Lỗi: {e}")
        else:
            st.info("👆 Hãy tải lên một bức ảnh chứa công thức toán hoặc đề bài để bắt đầu.")

    # CỘT 2: OUTPUT
    with col2:
        st.markdown("### 📄 **2. Kết quả Mã LaTeX**")
        if "result" in st.session_state and st.session_state["result"]:
            latex_code = st.session_state["result"]
            
            if "\\begin{tkz" in latex_code or "\\begin{tikzpicture}" in latex_code:
                st.warning("⚡ **Phát hiện mã đồ thị / Bảng biến thiên (TikZ/tkz-tab)**")
            
            st.code(latex_code, language="latex")
            
            st.markdown("**Chỉnh sửa nhanh mã:**")
            st.text_area(
                "Chỉnh sửa mã", 
                value=latex_code, 
                height=280, 
                label_visibility="collapsed"
            )
        else:
            render_empty_state()

if __name__ == "__main__":
    main()
