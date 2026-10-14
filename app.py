import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Apex AI - Executive Financial Analytics", layout="wide")

st.title("📊 Apex AI: Executive P&L & Financial Intelligence")
st.markdown("ระบบวิเคราะห์ข้อมูลทางการเงินระดับผู้บริหาร (CFO View) แบบเรียลไทม์ ขับเคลื่อนด้วย AI อัจฉริยะ")

@st.cache_data
def load_data():
    conn = sqlite3.connect("enterprise_poc.db")
    df = pd.read_sql("SELECT * FROM VW_Executive_PL_Analysis;", conn)
    conn.close()
    return df

try:
    df = load_data()
    st.subheader("📋 Executive P&L Summary Report")
    st.dataframe(df, use_container_width=True)

    st.subheader("📈 Financial Performance Visualization")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### เปรียบเทียบรายได้จริง vs งบประมาณ")
        fig_rev = px.bar(df, x="Period", y=["Revenue_Actual", "Revenue_Budget"], color="BU_Name", barmode="group")
        st.plotly_chart(fig_rev, use_container_width=True)

    with col2:
        st.markdown("#### อัตรากำไรจากการดำเนินงาน (%)")
        fig_margin = px.line(df, x="Period", y="Operating_Profit_Margin_Pct", color="BU_Name", markers=True)
        st.plotly_chart(fig_margin, use_container_width=True)

    st.subheader("💬 Apex AI: Financial Assistant Chat")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_query := st.chat_input("พิมพ์คำถามเชิงธุรกิจที่ต้องการวิเคราะห์แบบอิสระ (เช่น 'หน่วยธุรกิจไหนรายได้สูงสุด', 'เทียบต้นทุน', หรือชื่อ BU)"):
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            query_lower = user_query.lower()
            
            matched_bu = None
            for bu in df["BU_Name"].unique():
                if bu.lower() in query_lower:
                    matched_bu = bu
                    break
            
            if matched_bu:
                bu_data = df[df["BU_Name"] == matched_bu]
                latest_row = bu_data.iloc[-1]
                response = f"""
                📊 **Apex AI Analysis for {matched_bu}:**
                * **ช่วงเวลาล่าสุด ({latest_row['Period']}):** รายได้จริงอยู่ที่ `{latest_row['Revenue_Actual']:,.2f}` บาท (เทียบกับงบ `{latest_row['Revenue_Budget']:,.2f}` บาท)
                * **อัตรากำไรจากการดำเนินงาน:** `{latest_row['Operating_Profit_Margin_Pct']:.2f}%`
                * **ความเห็นเชิงกลยุทธ์:** หน่วยธุรกิจนี้มีอัตราความเบี่ยงเบนของรายได้ `{latest_row['Revenue_Variance_Pct']}%` แนะนำให้ผู้บริหารติดตามค่าใช้จ่าย OpEx ที่ระดับ `{latest_row['OpEx_Actual']:,.2f}` บาทอย่างใกล้ชิด
                """
            elif "สูงสุด" in query_lower or "best" in query_lower or "top" in query_lower:
                top_row = df.loc[df["Revenue_Actual"].idxmax()]
                response = f"""
                📊 **Apex AI Insights (Highest Revenue):**
                * หน่วยธุรกิจที่ทำรายได้จริงสูงสุดคือ **{top_row['BU_Name']}** ในช่วงงวด `{top_row['Period']}`
                * ทำยอดรายได้สูงถึง `{top_row['Revenue_Actual']:,.2f}` บาท โดยมีอัตรากำไรจากการดำเนินงานอยู่ที่ `{top_row['Operating_Profit_Margin_Pct']:.2f}%`
                """
            elif "ต้นทุน" in query_lower or "opex" in query_lower:
                total_opex = df["OpEx_Actual"].sum()
                avg_opex_var = df["OpEx_Variance_Pct"].mean()
                response = f"""
                📊 **Apex AI Cost Analysis (OpEx):**
                * ยอดรวมต้นทุนการดำเนินงาน (OpEx Actual) ทั้งหมดในระบบอยู่ที่ `{total_opex:,.2f}` บาท
                * ค่าเฉลี่ยความเบี่ยงเบนของต้นทุนจากงบประมาณอยู่ที่ `{avg_opex_var:.2f}%` ควบคุมทิศทางค่าใช้จ่ายภาพรวมได้ตามกรอบนโยบายองค์กร
                """
            else:
                total_rev = df["Revenue_Actual"].sum()
                response = f"""
                📊 **Apex AI Executive Summary:**
                * จากคำถามของคุณ ระบบได้สแกนฐานข้อมูล P&L พบยอดรายได้รวมสะสมอยู่ที่ `{total_rev:,.2f}` บาท 
                * คุณสามารถพิมพ์เจาะจงชื่อหน่วยธุรกิจ (เช่น **Core Banking**, **Digital Payment**) หรือถามเรื่องรายได้ กำไร และต้นทุนได้ทันทีครับ
                """
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
except Exception as e:
    st.error(f"เกิดข้อผิดพลาด: {e}")
