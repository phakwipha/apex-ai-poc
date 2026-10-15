import anthropic
import pandas as pd
import sqlite3
import streamlit as st

# ตั้งค่าหน้าเว็บ
st.set_page_config(
    page_title="Executive P&L Dashboard", page_icon="📊", layout="wide"
)

st.markdown(
    """
    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: #1f2937; margin-bottom: 5px;'>📊 Executive P&L & Financial Intelligence Dashboard</h1>
        <p style='color: #4b5563; font-size: 16px;'>ระบบรายงานผู้บริหารและผู้ช่วยวิเคราะห์ข้อมูลอัตโนมัติ (Powered by Claude 3 Haiku)</p>
    </div>
""",
    unsafe_allow_html=True,
)


# เชื่อมต่อ SQLite และดึงข้อมูล
@st.cache_data
def load_data():
  conn = sqlite3.connect("enterprise_poc.db")
  df = pd.read_sql("SELECT * FROM pnl_data", conn)
  conn.close()
  return df


try:
  df = load_data()
except Exception as e:
  st.error(
      f"ไม่พบฐานข้อมูล enterprise_poc.db หรือตาราง pnl_data: {e}"
  )
  st.stop()

# ส่วนเชื่อมต่อ Claude API
if "ANTHROPIC_API_KEY" not in st.secrets:
  st.error("❌ กรุณาตั้งค่า ANTHROPIC_API_KEY ใน Streamlit Secrets ให้เรียบร้อย")
  st.stop()

client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

# ตัวอย่างช่องถาม-ตอบข้อมูลงบการเงิน
question = st.selectbox(
    "💡 เลือกคำถามวิเคราะห์ด่วน หรือพิมพ์คำถามของคุณ:",
    [
        "BU ไหนกำไรสูงสุด",
        "ภาพรวมรายได้และกำไรสุทธิเทียบกับงบประมาณเป็นอย่างไร",
        "หน่วยงานใดที่มีค่าใช้จ่ายสูงผิดปกติ",
    ],
)

if st.button("วิเคราะห์ข้อมูลด้วย AI", type="primary"):
  with st.spinner("กำลังวิเคราะห์ข้อมูลการเงิน..."):
    # แปลงข้อมูลตัวอย่างบางส่วนให้ AI อ่านเข้าใจบริบท
    data_summary = df.head(20).to_string(index=False)
    prompt = f"""
        คุณคือผู้ช่วยผู้บริหารด้านการเงิน วิเคราะห์ข้อมูล P&L ต่อไปนี้เพื่อตอบคำถาม: "{question}"
        
        ข้อมูลตัวอย่าง (ตาราง pnl_data):
        {data_summary}
        
        กรุณาตอบเป็นภาษาไทย กระชับ ชัดเจน และเป็นมืออาชีพสำหรับผู้บริหาร
        """

    try:
      response = client.messages.create(
          model="claude-3-haiku-20240307",
          max_tokens=400,
          messages=[{"role": "user", "content": prompt}],
      )
      st.markdown("### 🤖 ผลการวิเคราะห์")
      st.info(response.content[0].text)
    except Exception as e:
      st.error(f"เกิดข้อผิดพลาดในการประมวลผล: {e}")

# แสดงตารางข้อมูลเบื้องต้นด้านล่าง
with st.expander("📁 ดูข้อมูลดิบทั้งหมดในระบบ (Raw Data)"):
  st.dataframe(df, use_container_width=True)
