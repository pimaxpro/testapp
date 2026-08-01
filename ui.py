import re
import streamlit as st
from gemini_service import GeminiAPIService
from config import DEFAULT_EXTRA_PROMPT

class UIComponent:
    @staticmethod
    def render_header():
        st.markdown("<h1 class='header-title'>Math OCR Pro Studio</h1>", unsafe_allow_html=True)
        st.markdown("Chuyển đổi **Ảnh / PDF** thành mã **LaTeX (ex_test, TikZ)** chuẩn định dạng.")
        st.write("")

    @staticmethod
    def render_sidebar(api_service: GeminiAPIService):
        with st.sidebar:
            st.markdown("## :material/settings: Cấu hình hệ thống")
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
                help="Key sẽ được tự động lưu trên trình duyệt."
            )
            
            if api_key_input != st.session_state.get("api_key", ""):
                st.session_state["api_key"] = api_key_input
                st.query_params["api_key"] = api_key_input
                st.rerun()

            if api_key_input:
                st.caption(":material/check_circle: *Đã kết nối API Key*")

            st.markdown("---")

            mode = st.selectbox(
                "Chế độ xử lý",
                options=["ex_test", "ex_test_solve", "tikz"],
                format_func=lambda x: {
                    "ex_test": "📄 Soạn đề ex_test",
                    "ex_test_solve": "🧠 ex_test + Tự giải",
                    "tikz": "🎨 Chuyển hình -> TikZ"
                }[x]
            )

            available_models = api_service.get_available_models() if api_key_input else ["Vui lòng nhập API Key"]
            model_choice = st.selectbox("Mô hình Vision", available_models, index=0)

            st.markdown("---")

            if "extra_notes_val" not in st.session_state:
                st.session_state["extra_notes_val"] = DEFAULT_EXTRA_PROMPT

            extra_notes = st.text_area(
                "Yêu cầu định dạng bổ sung", 
                value=st.session_state["extra_notes_val"],
                height=120
            )
            st.session_state["extra_notes_val"] = extra_notes

            return api_key_input, mode, model_choice, extra_notes

    @staticmethod
    def render_editor_section():
        st.markdown("### :material/terminal: Overleaf-style LaTeX Editor")

        current_code = st.session_state.get("result", "")

        if not current_code:
            st.markdown(
                """
                <div style="background-color: #1e1e1e; border: 1px dashed #444; border-radius: 8px; padding: 50px 20px; text-align: center; color: #888; margin-top: 10px;">
                    <p style="font-size: 32px; margin-bottom: 5px;">💻</p>
                    <p style="font-family: Consolas, monospace; font-size: 13px;">// Mã LaTeX sau khi OCR sẽ hiển thị ở đây với giao diện Overleaf...</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
            return

        # --- TOOLBAR PHONG CÁCH OVERLEAF ---
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
        with c1:
            st.download_button(
                "📥 Tải .tex", 
                data=current_code, 
                file_name="main.tex", 
                mime="text/x-tex",
                use_container_width=True
            )
        with c2:
            if st.button("🔄 Undo OCR", use_container_width=True, help="Reset về bản gốc"):
                st.session_state["result"] = st.session_state.get("raw_result", "")
                st.rerun()
        with c3:
            if st.button("🧹 Format Space", use_container_width=True):
                cleaned = re.sub(r'\n\s*\n', '\n', current_code)
                st.session_state["result"] = cleaned.strip()
                st.rerun()
        with c4:
            if st.button("💬 Comment %", use_container_width=True):
                lines = current_code.split('\n')
                if lines[0].startswith('%'):
                    lines = [l[1:] if l.startswith('%') else l for l in lines]
                else:
                    lines = ['%' + l for l in lines]
                st.session_state["result"] = '\n'.join(lines)
                st.rerun()
        with c5:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state["result"] = ""
                st.rerun()

        # BAR CHÈN SNIPPETS
        st.caption("🚀 **Snippet Cú Pháp:**")
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            if st.button("+ \\begin{ex}", use_container_width=True):
                st.session_state["result"] += "\n\\begin{ex}\n\n\\end{ex}"
                st.rerun()
        with s2:
            if st.button("+ \\choice", use_container_width=True):
                st.session_state["result"] += "\n\\choice{A}{B}{C}{D}"
                st.rerun()
        with s3:
            if st.button("+ \\loigiai", use_container_width=True):
                st.session_state["result"] += "\n\\loigiai{\n\n}"
                st.rerun()
        with s4:
            if st.button("+ TikZ Plot", use_container_width=True):
                snippet = "\n\\begin{tikzpicture}[line cap=round,line join=round,font=\\scriptsize,>=stealth']\n" \
                          "   \\tikzset{declare function={f(\\x)=\\x^2 - 2*\\x;}}\n" \
                          "   \\begin{scope}\n" \
                          "       \\clip (-3,-3) rectangle (3,3);\n" \
                          "       \\draw[samples=100] plot[domain=-3:3] (\\x, {f(\\x)});\n" \
                          "   \\end{scope}\n" \
                          "\\end{tikzpicture}"
                st.session_state["result"] += snippet
                st.rerun()
        with s5:
            if st.button("+ Bảng BBT", use_container_width=True):
                snippet = "\n\\begin{tikzpicture}\n" \
                          "   \\tkzTabInit{$x$ /1, $y'$ /1, $y$ /2}{$-\\infty$, $0$, $+\\infty$}\n" \
                          "   \\tkzTabLine{, +, z, -, }\n" \
                          "   \\tkzTabVar{-/ $-\\infty$, +/ $1$, -/ $-\\infty$}\n" \
                          "\\end{tikzpicture}"
                st.session_state["result"] += snippet
                st.rerun()

        # FIND & REPLACE OVERLEAF STYLE
        with st.expander("🔍 Tìm kiếm & Thay thế"):
            f_col1, f_col2, f_col3 = st.columns([4, 4, 2])
            find_txt = f_col1.text_input("Find", key="f_in")
            replace_txt = f_col2.text_input("Replace", key="r_in")
            if f_col3.button("Replace All", use_container_width=True):
                if find_txt:
                    st.session_state["result"] = current_code.replace(find_txt, replace_txt)
                    st.rerun()

        # --- MAIN OVERLEAF CODE EDITOR ---
        edited_code = st.text_area(
            "Mã LaTeX Editor",
            value=current_code,
            height=520,
            key="overleaf_editor",
            label_visibility="collapsed"
        )

        if edited_code != current_code:
            st.session_state["result"] = edited_code

        # STATUS BAR DƯỚI EDITOR
        num_lines = len(edited_code.split('\n'))
        num_chars = len(edited_code)
        num_ex = edited_code.count(r'\begin{ex}')

        st.caption(
            f"🟢 **Overleaf Engine Active** | {num_lines} lines | {num_chars} chars | "
            f"Found **{num_ex}** `ex` environments"
        )
