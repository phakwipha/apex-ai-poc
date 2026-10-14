import sqlite3
import google.generativeai as genai
import pandas as pd
import streamlit as st

# ตั้งค่า API Key จาก Secrets
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")


def get_available_model():
    # ค้นหาโมเดลที่รองรับ generateContent ในบัญชีของคุณอัตโนมัติ
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            return m.name
    return "gemini-1.5-flash"  # ค่าสำรอง


def run_nl2sql(user_query):
    schema_info = """
    Table Name: financial_summary
    Columns:
    - Period (TEXT): e.g. '2026-08', '2026-09'
    - BU_Name (TEXT): e.g. 'Core Banking', 'Digital Payment'
    - Revenue_Actual (REAL)
    - Revenue_Budget (REAL)
    - Operating_Profit (REAL)
    """

    prompt = f"""
    You are an expert SQLite Data Analyst. 
    Based on the DB Schema below, generate ONLY a valid SQLite query to answer the user's question.
    Do not include markdown syntax like ```sql or explanation. Output raw SQL query string only.
    
    Schema:
    {schema_info}
    
    User Question: {user_query}
    """

    # เลือกโมเดลที่รองรับจากระบบอัตโนมัติ ไม่ต้องกลัวใส่ชื่อผิด
    model_name = get_available_model()
    model = genai.GenerativeModel(model_name)

    response = model.generate_content(prompt)
    sql_query = response.text.strip().replace("```sql", "").replace("```", "")

    conn = sqlite3.connect("enterprise_poc.db")
    df_result = pd.read_sql_query(sql_query, conn)
    conn.close()

    return sql_query, df_result


# ---- Dashboard UI ----
st.title("📊 Executive P&L & Financial Intelligence Dashboard")
st.write("ระบบรายงานผู้บริหารและผู้ช่วยวิเคราะห์ข้อมูลอัตโนมัติ")

user_input = st.chat_input(
    "พิมพ์คำถามเชิงธุรกิจ (เช่น 'ขอผลกำไรของ Core Banking เดือน 2026-08')"
)

if user_input:
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        try:
            sql, result_df = run_nl2sql(user_input)
            st.markdown(f"**Generated SQL:** `{sql}`")
            if not result_df.empty:
                st.dataframe(result_df)
            else:
                st.write("ไม่พบข้อมูลตามเงื่อนไขที่ระบุ")
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")
