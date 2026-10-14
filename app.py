import time
import sqlite3
from google import genai
import pandas as pd
import streamlit as st

if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")


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

    # เพิ่มระบบพยายามส่งซ้ำอัตโนมัติ (Retry) เมื่อเจอเซิร์ฟเวอร์หนาแน่น (503)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash", contents=prompt
            )
            sql_query = (
                response.text.strip().replace("```sql", "").replace("```", "")
            )

            conn = sqlite3.connect("enterprise_poc.db")
            df_result = pd.read_sql_query(sql_query, conn)
            conn.close()

            return sql_query, df_result
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(2)  # รอ 2 วินาทีก่อนลองใหม่
                continue
            else:
                raise e


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
