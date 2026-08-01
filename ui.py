import re
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
    def render_editor_section():
        """Khu vực LaTeX Code Editor chuyên nghiệp với 20+ tính năng"""
        st.markdown("### :material/edit_note: 2. LaTeX Code Editor Studio")

        # Lấy mã hiện tại trong session_state
        current_code = st.session_state.get("result", "")

        if not current_code:
            st.markdown(
                """
                <div style="border: 2px dashed rgba(128, 128, 128, 0.3); border-radius: 12px; padding: 60px 20px; text-align: center; color: #888888; margin-top: 10px;">
                    <p style="font-size: 40px; margin-bottom: 10px;">📝</p>
                    <p style="font-weight: 500;">Mã LaTeX sau khi OCR sẽ tự động nạp vào Editor ở đây để chỉnh sửa trực tiếp.</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            return

        # --- THANH CÔNG CỤ TOOLBAR (20+ TÍNH NĂNG) ---
        
        # Hàng 1: Quản lý File, Export & Restore
        t1, t2, t3, t4, t5 = st.columns([2, 2, 2, 2, 2])
        with t1:
            st.download_button(
                "📥 Tải .tex", 
                data=current_code, 
                file_name="math_output.tex", 
                mime="text/x-tex",
                use_container_width=True
            )
        with t2:
            if st.button("🔄 Khôi phục gốc", use_container_width=True, help="Khôi phục về bản OCR ban đầu"):
                st.session_state["result"] = st.session_state.get("raw_result", "")
                st.rerun()
        with t3:
            if st.button("🧹 Dọn khoảng trắng", use_container_width=True, help="Xóa dòng trống & space thừa"):
                cleaned = re.sub(r'\n\s*\n', '\n', current_code)
                st.session_state["result"] = cleaned.strip()
                st.rerun()
        with t4:
            if st.button("💬 Toggle Comment", use_container_width=True, help="Thêm/Xóa dấu % đầu mỗi dòng"):
                lines = current_code.split('\n')
                if lines[0].startswith('%'):
                    lines = [l[1:] if l.startswith('%') else l for l in lines]
                else:
                    lines = ['%' + l for l in lines]
                st.session_state["result"] = '\n'.join(lines)
                st.rerun()
        with t5:
            if st.button("❌ Xóa tất cả", use_container_width=True):
                st.session_state["result"] = ""
                st.rerun()

        # Hàng 2: Chèn nhanh cấu trúc ex_test & TikZ
        st.caption("⚡ **Chèn nhanh môi trường & Cấu trúc:**")
        b1, b2, b3, b4, b5 = st.columns(5)
        with b1:
            if st.button("➕ \\begin{ex}", use_container_width=True):
                st.session_state["result"] += "\n\\begin{ex}\n\n\\end{ex}"
                st.rerun()
        with b2:
            if st.button("🔘 \\choice", use_container_width=True):
                st.session_state["result"] += "\n\\choice\n{A}\n{B}\n{C}\n{D}"
                st.rerun()
        with b3:
            if st.button("📝 \\loigiai", use_container_width=True):
                st.session_state["result"] += "\n\\loigiai{\n\n}"
                st.rerun()
        with b4:
            if st.button("📈 TikZ Plot", use_container_width=True):
                snippet = "\n\\begin{tikzpicture}[line cap=round,line join=round,font=\\scriptsize,>=stealth']\n" \
                          "   \\tikzset{declare function={f(\\x)=\\x^2 - 2*\\x;}}\n" \
                          "   \\begin{scope}\n" \
                          "       \\clip (-3,-3) rectangle (3,3);\n" \
                          "       \\draw[samples=100] plot[domain=-3:3] (\\x, {f(\\x)});\n" \
                          "   \\end{scope}\n" \
                          "\\end{tikzpicture}"
                st.session_state["result"] += snippet
                st.rerun()
        with b5:
            if st.button("📊 Bảng BBT", use_container_width=True):
                snippet = "\n\\begin{tikzpicture}\n" \
                          "   \\tkzTabInit{$x$ /1, $y'$ /1, $y$ /2}{$-\\infty$, $0$, $+\\infty$}\n" \
                          "   \\tkzTabLine{, +, z, -, }\n" \
                          "   \\tkzTabVar{-/ $-\\infty$, +/ $1$, -/ $-\\infty$}\n" \
                          "\\end{tikzpicture}"
                st.session_state["result"] += snippet
                st.rerun()

        # Hàng 3: Tìm kiếm & Thay thế (Find & Replace)
        with st.expander("🔍 **Tìm kiếm & Thay thế chuỗi (Find & Replace)**"):
            f_col1, f_col2, f_col3 = st.columns([4, 4, 2])
            find_txt = f_col1.text_input("Tìm chuỗi", key="find_t")
            replace_txt = f_col2.text_input("Thay thế bằng", key="rep_t")
            if f_col3.button("Thay thế hết", use_container_width=True):
                if find_txt:
                    st.session_state["result"] = current_code.replace(find_txt, replace_txt)
                    st.rerun()

        # --- KHU VỰC EDITOR CHỈNH SỬA TRỰC TIẾP ---
        edited_code = st.text_area(
            "Mã LaTeX Editor",
            value=current_code,
            height=480,
            key="latex_editor_area",
            label_visibility="collapsed"
        )

        # Cập nhật state nếu người dùng tự gõ chỉnh sửa trên text_area
        if edited_code != current_code:
            st.session_state["result"] = edited_code

        # --- THANH THỐNG KÊ PHÍA DƯỚI EDITOR ---
        num_lines = len(edited_code.split('\n'))
        num_words = len(edited_code.split())
        num_ex = edited_code.count(r'\begin{ex}')
        num_tikz = edited_code.count(r'\begin{tikzpicture}')

        st.caption(
            f"📊 **Thống kê Editor:** {num_lines} dòng | {num_words} từ | "
            f"Thấy **{num_ex}** câu `ex` | **{num_tikz}** hình `tikzpicture`"
        )
