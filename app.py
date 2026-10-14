import sqlite3
import google.generativeai as genai
import pandas as pd
import streamlit as st

# ตั้งค่า API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


def run_nl2sql(user_query):
    schema_info = """
    Table Name: financial_summary
    Columns:
    - Period (TEXT)
    - BU_Name (TEXT)
    - Revenue_Actual (REAL)
    - Revenue_Budget (REAL)
    - Operating_Profit (REAL)
    """

    prompt = f"""
    Generate only a valid SQLite query for the question based on this schema:
    {schema_info}
    Question: {user_query}
    Output only the raw SQL string without markdown.
    """

    # ใช้โมเดลพื้นฐานที่เสถียรที่สุด
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    sql_query = response.text.strip().replace("```sql", "").replace("```", "")

    conn = sqlite3.connect("enterprise_poc.db")
    df_result = pd.read_sql_query(sql_query, conn)
    conn.close()

    return sql_query, df_result


st.title("📊 Executive P&L & Financial Intelligence Dashboard")

user_input = st.chat_input("พิมพ์คำถามเชิงธุรกิจที่นี่...")

if user_input:
    st.chat_message("user").write(user_input)
    with st.chat_message("assistant"):
        try:
            sql, result_df = run_nl2sql(user_input)
            st.code(sql, language="sql")
            st.dataframe(result_df)
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาด: {e}")
