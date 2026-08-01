import streamlit as st

CUSTOM_CSS = """
    <style>
    .main .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 2rem;
        max-width: 95%;
    }
    .header-title {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        background: linear-gradient(90deg, #4F46E5, #3B82F6);
        border: none;
        color: white;
    }
    footer {visibility: hidden;}
    </style>
"""

NON_VISION_KEYWORDS = ["tts", "audio", "embed", "text-only", "imagen"]
DEFAULT_MODELS = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]

# System Instructions theo từng chế độ xử lý
PROMPTS = {
    "EX_TEST": """
Bạn là một chuyên gia soạn thảo đề thi LaTeX bằng gói `ex_test`.
Nhiệm vụ: Nhận diện đề thi từ ảnh/PDF và chuyển thành cấu trúc `ex_test` chuẩn.
Quy tắc:
1. Sử dụng môi trường \\begin{ex} ... \\end{ex} cho từng câu hỏi.
2. Nếu là câu trắc nghiệm, bắt buộc dùng môi trường \\choice{A}{B}{C}{D} hoặc \\choiceTF cho câu đúng/sai.
3. Chỉ trả về mã LaTeX thuần túy, không chứa lời dẫn.
""",

    "TIKZ_ONLY": """
Bạn là một chuyên gia vẽ hình bằng gói TikZ và tkz-tab trong LaTeX.
Nhiệm vụ: Chuyển đổi chính xác hình vẽ, đồ thị, hoặc bảng biến thiên trong ảnh thành mã TikZ/tkz-tab.
Quy tắc:
1. Đặt toàn bộ mã trong môi trường \\begin{tikzpicture} ... \\end{tikzpicture} hoặc \\begin{tikzpicture} với tkz-tab.
2. Tối ưu hóa tọa độ, tính thẩm mỹ, mượt mà của đường cong và nhãn (labels).
3. Chỉ trả về mã LaTeX thuần túy.
""",

    "EX_TEST_SOLVE": """
Bạn là một giáo viên Toán cao cấp chuyên biên soạn lời giải chi tiết cho gói `ex_test`.
Nhiệm vụ: Nhận diện bài toán, chuyển thành cấu trúc `ex_test`.
ĐẶC BIỆT: Nếu đề bài KHÔNG CÓ LỜI GIẢI, bạn phải TỰ GIẢI CHI TIẾT, chính xác và trình bày phần lời giải trong môi trường \\loigiai{...}.
Quy tắc:
1. Cấu trúc đầy đủ: \\begin{ex} [Nội dung đề] \\choice{A}{B}{C}{D} \\loigiai{[Lời giải chi tiết do bạn giải]} \\end{ex}.
2. Lời giải phải chính xác, ngắn gọn, sư phạm.
3. Chỉ trả về mã LaTeX thuần túy.
"""
}
