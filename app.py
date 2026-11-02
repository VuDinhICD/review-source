import os
import re
import html
import difflib
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from google import genai

# Cấu hình giao diện Streamlit rộng toàn màn hình
st.set_page_config(
    page_title="ServiceNow Code Review - Git Side-by-Side Diff",
    page_icon="🔍",
    layout="wide"
)

load_dotenv()
SN_INSTANCE = (os.getenv("SN_INSTANCE") or "").rstrip("/")
SN_USER = os.getenv("SN_USER")
SN_PASSWORD = os.getenv("SN_PASSWORD")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def fetch_script_include(script_name=None):
    """Lấy Script Include từ ServiceNow Table API"""
    url = f"{SN_INSTANCE}/api/now/table/sys_script_include"
    headers = {"Accept": "application/json"}
    query = f"name={script_name.strip()}" if script_name else "ORDERBYDESCsys_updated_on"
    params = {
        "sysparm_limit": 1,
        "sysparm_query": query,
        "sysparm_fields": "sys_id,name,client_callable,access,script"
    }
    
    response = requests.get(url, auth=(SN_USER, SN_PASSWORD), headers=headers, params=params, timeout=15)
    response.raise_for_status()
    results = response.json().get("result", [])
    return results[0] if results else None

def review_with_gemini(record):
    """Gửi code sang Gemini để phân tích SOLID và trích xuất code refactor"""
    prompt = f"""
    Bạn là ServiceNow Certified Master Architect. Hãy review Script Include sau:
    - Tên: {record['name']}
    - Client Callable: {record.get('client_callable', 'false')}
    - Access Level: {record.get('access', 'package_private')}

    Mã nguồn gốc:
    ```javascript
    {record['script']}
    ```

    CẤU TRÚC PHẢN HỒI BẮT BUỘC (Chia đúng 2 phần):

    ### PHẦN 1: ĐÁNH GIÁ KỸ THUẬT & SOLID
    - Cấu trúc & Security (AbstractAjaxProcessor, validate tham số).
    - Hiệu năng (Tránh GlideRecord lồng nhau, GlideAggregate, try/catch).
    - Phân tích SOLID (Single Responsibility, Open/Closed, Dependency Inversion,...).
    - Tóm tắt các dòng hoặc logic cần gỡ bỏ/sửa đổi.

    ### PHẦN 2: REFACTORED_CODE
    Bắt buộc cung cấp toàn bộ mã nguồn JavaScript hoàn chỉnh đã sửa bên trong khối mã:
    ```javascript
    // Toàn bộ code refactor ở đây
    ```
    """
    response = ai_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def extract_refactored_code(gemini_text):
    """Trích xuất khối mã javascript từ phản hồi của Gemini"""
    blocks = re.findall(r"```javascript(.*?)```", gemini_text, re.DOTALL)
    if blocks:
        return blocks[-1].strip()
    return ""

def render_side_by_side_diff(orig_code, new_code):
    """Sinh mã HTML/CSS hiển thị Side-by-Side Diff chuẩn phong cách Git/VS Code"""
    orig_lines = orig_code.splitlines()
    new_lines = new_code.splitlines()

    matcher = difflib.SequenceMatcher(None, orig_lines, new_lines)
    left_rows = []
    right_rows = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for i, j in zip(range(i1, i2), range(j1, j2)):
                left_rows.append((i + 1, html.escape(orig_lines[i]), "normal"))
                right_rows.append((j + 1, html.escape(new_lines[j]), "normal"))
        elif tag == 'delete':
            for i in range(i1, i2):
                left_rows.append((i + 1, html.escape(orig_lines[i]), "delete"))
                right_rows.append(("", "", "gap"))
        elif tag == 'insert':
            for j in range(j1, j2):
                left_rows.append(("", "", "gap"))
                right_rows.append((j + 1, html.escape(new_lines[j]), "insert"))
        elif tag == 'replace':
            len_del = i2 - i1
            len_ins = j2 - j1
            max_len = max(len_del, len_ins)
            for k in range(max_len):
                if k < len_del:
                    left_rows.append((i1 + k + 1, html.escape(orig_lines[i1 + k]), "delete"))
                else:
                    left_rows.append(("", "", "gap"))
                
                if k < len_ins:
                    right_rows.append((j1 + k + 1, html.escape(new_lines[j1 + k]), "insert"))
                else:
                    right_rows.append(("", "", "gap"))

    # Dựng HTML cho từng bên
    def build_table_rows(rows):
        html_out = ""
        for line_num, code, style in rows:
            cls = ""
            if style == "delete":
                cls = "del-line"
            elif style == "insert":
                cls = "add-line"
            elif style == "gap":
                cls = "gap-line"
            
            num_str = str(line_num) if line_num != "" else ""
            html_out += f"""<tr class="{cls}">
                <td class="line-num">{num_str}</td>
                <td class="line-code">{code}</td>
            </tr>"""
        return html_out

    left_html = build_table_rows(left_rows)
    right_html = build_table_rows(right_rows)
    total_lines = len(left_rows)
    calc_height = min(750, max(350, total_lines * 22 + 50))

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: #d4d4d4;
            font-family: Consolas, "Courier New", monospace;
            font-size: 13px;
        }}
        .diff-container {{
            display: flex;
            width: 100%;
            border: 1px solid #333;
            background-color: #1e1e1e;
            overflow-x: auto;
        }}
        .diff-pane {{
            width: 50%;
            box-sizing: border-box;
            overflow-x: auto;
        }}
        .diff-pane:first-child {{
            border-right: 2px solid #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        tr {{
            height: 22px;
        }}
        td {{
            padding: 0 4px;
            white-space: pre;
            vertical-align: middle;
        }}
        .line-num {{
            width: 48px;
            text-align: right;
            padding-right: 10px;
            color: #858585;
            user-select: none;
            background-color: #1e1e1e;
            border-right: 1px solid #2d2d2d;
        }}
        .line-code {{
            padding-left: 8px;
        }}
        /* Dòng bị xóa: Nền đỏ rực như trong Git / VS Code */
        .del-line {{
            background-color: rgba(205, 49, 49, 0.35) !important;
        }}
        .del-line .line-num {{
            background-color: rgba(205, 49, 49, 0.45) !important;
            color: #ff8585;
        }}
        .del-line .line-code {{
            color: #ffcccc;
        }}
        /* Dòng thêm mới: Nền xanh lá */
        .add-line {{
            background-color: rgba(46, 160, 67, 0.3) !important;
        }}
        .add-line .line-num {{
            background-color: rgba(46, 160, 67, 0.45) !important;
            color: #85e89d;
        }}
        .add-line .line-code {{
            color: #dcffe4;
        }}
        /* Dòng trống: Vân sọc chéo chuẩn Git/VS Code */
        .gap-line {{
            background: repeating-linear-gradient(
                -45deg,
                #1e1e1e,
                #1e1e1e 6px,
                #282828 6px,
                #282828 12px
            ) !important;
        }}
        .gap-line .line-num {{
            background-color: #1b1b1b;
        }}
    </style>
    </head>
    <body>
        <div class="diff-container">
            <div class="diff-pane">
                <table>{left_html}</table>
            </div>
            <div class="diff-pane">
                <table>{right_html}</table>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template, calc_height

# --- GIAO DIỆN CHÍNH ---
st.title("ServiceNow Code Reviewer (Side-by-Side Diff)")

if not all([SN_INSTANCE, SN_USER, SN_PASSWORD, GEMINI_API_KEY]):
    st.error("⚠️ Vui lòng kiểm tra file `.env`: thiếu cấu hình SN_INSTANCE, SN_USER, SN_PASSWORD hoặc GEMINI_API_KEY.")
    st.stop()

col_input, col_action = st.columns([4, 1])
with col_input:
    script_name_input = st.text_input(
        label="Tên Script Include:",
        placeholder="Nhập tên Script Include (bỏ trống để lấy script cập nhật gần nhất)..."
    )
with col_action:
    st.write("##")
    btn_start = st.button("🚀 Bắt đầu Review", use_container_width=True, type="primary")

if btn_start:
    with st.spinner("Đang lấy code và phân tích..."):
        try:
            record = fetch_script_include(script_name_input if script_name_input.strip() else None)
            
            if not record:
                st.warning(f"Không tìm thấy Script Include nào phù hợp với từ khóa: `{script_name_input}`")
            else:
                original_code = record.get("script", "")
                raw_response = review_with_gemini(record)
                refactored_code = extract_refactored_code(raw_response)
                
                # Bóc tách phần đánh giá hiển thị lên trên
                review_analysis = re.sub(r"### PHẦN 2: REFACTORED_CODE.*", "", raw_response, flags=re.DOTALL)

                # ==========================================
                # 1. PHẦN KẾT QUẢ REVIEW (TRÊN CÙNG - RỘNG 100%)
                # ==========================================
                st.markdown("---")
                st.subheader(f"📋 Báo cáo Review Script Include: `{record['name']}`")
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**Client Callable:** `{record.get('client_callable')}`")
                c2.markdown(f"**Access:** `{record.get('access')}`")
                c3.markdown(f"**Instance:** `{SN_INSTANCE}`")
                
                st.markdown(review_analysis)

                # ==========================================
                # 2. KHU VỰC DIFF SIDE-BY-SIDE (Ở DƯỚI)
                # ==========================================
                st.markdown("---")
                st.subheader("🔄 So sánh thay đổi (Side-by-Side Changes)")
                st.caption("🔴 **Bên trái (Mã gốc):** Dòng bị xóa tô màu đỏ | 🟢 **Bên phải (Refactor):** Dòng thêm mới tô xanh lá | ⬛ **Vân sọc chéo:** Khoảng trống dòng tương ứng")

                diff_html, diff_height = render_side_by_side_diff(original_code, refactored_code)
                components.html(diff_html, height=diff_height, scrolling=True)

                with st.expander("📋 Xem toàn bộ mã nguồn sau Refactor (để copy nhanh)"):
                    st.code(refactored_code, language="javascript", line_numbers=True)

        except requests.exceptions.HTTPError as err:
            st.error(f"Lỗi ServiceNow: {err}")
        except Exception as e:
            st.error(f"Đã xảy ra lỗi: {e}")