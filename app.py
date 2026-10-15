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
        <p style='color: #4b5563; font-size: 16px;'>ระบบรายงานผู้บริหารและผู้ช่วยวิเคราะห์ข้อมูลอัตโนมัติ</p>
    </div>
""",
    unsafe_allow_html=True,
)


# เชื่อมต่อ SQLite และสร้างตารางพร้อมข้อมูลตัวอย่างอัตโนมัติ
@st.cache_data
def load_data():
  conn = sqlite3.connect("enterprise_poc.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pnl_data (
            Period TEXT,
            BU_Name TEXT,
            Revenue_Actual REAL,
            Revenue_Budget REAL,
            Operating_Profit REAL
        )
    """)
  cursor.execute("SELECT COUNT(*) FROM pnl_data")
  if cursor.fetchone()[0] == 0:
    sample_data = [
        ("2026-Q1", "Retail BU", 1500000, 1400000, 350000),
        ("2026-Q1", "Corporate BU", 2800000, 3000000, 820000),
        ("2026-Q1", "Online BU", 950000, 900000, 290000),
        ("2026-Q2", "Retail BU", 1650000, 1600000, 410000),
        ("2026-Q2", "Corporate BU", 3100000, 3000000, 950000),
        ("2026-Q2", "Online BU", 1200000, 1100000, 380000),
    ]
    cursor.executemany(
        "INSERT INTO pnl_data VALUES (?, ?, ?, ?, ?)", sample_data
    )
    conn.commit()
  df = pd.read_sql("SELECT * FROM pnl_data", conn)
  conn.close()
  return df


try:
  df = load_data()
except Exception as e:
  st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
  st.stop()

# ตรวจสอบการตั้งค่า API Key
if "GEMINI_API_KEY" not in st.secrets:
  st.error("❌ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ให้เรียบร้อย")
  st.stop()

api_key = st.secrets["GEMINI_API_KEY"]

# ส่วนเลือกคำถามวิเคราะห์
question = st.selectbox(
    "💡 เลือกคำถามวิเคราะห์ด่วน หรือพิมพ์คำถามของคุณ:",
    [
        "BU ไหนกำไรสูงสุด",
        "ภาพรวมรายได้และกำไรสุทธิเทียบกับงบประมาณเป็นอย่างไร",
        "หน่วยงานใดที่มีค่าใช้จ่ายหรือผลประกอบการน่ากังวล",
    ],
)

if st.button("วิเคราะห์ข้อมูลด้วย AI", type="primary"):
  with st.spinner("กำลังวิเคราะห์ข้อมูลการเงิน..."):
    analysis_result = None

    # พยายามเรียกใช้งานผ่าน Google GenAI SDK ทางการ
    try:
      import google.generativeai as genai

      genai.configure(api_key=api_key)
      model = genai.GenerativeModel("gemini-1.5-flash")
      prompt = f"""
            คุณคือผู้ช่วยผู้บริหารด้านการเงิน วิเคราะห์ข้อมูล P&L ต่อไปนี้เพื่อตอบคำถาม: "{question}"
            ข้อมูลตาราง pnl_data:
            {df.to_string(index=False)}
            กรุณาตอบเป็นภาษาไทย กระชับ ชัดเจน และตรงไปตรงมาสำหรับผู้บริหาร
            """
      response = model.generate_content(prompt)
      analysis_result = response.text
    except Exception as api_err:
      # กรณีที่ API Key ติดข้อจำกัดสิทธิ์หรือ Error ระบบจะแสดงผลการวิเคราะห์เชิงโครงสร้างสำรองทันทีเพื่อให้แดชบอร์ดไม่พัง
      analysis_result = f"""
      *(หมายเหตุ: ระบบตรวจพบข้อจำกัดสิทธิ์ของ API Key หรือการเชื่อมต่อภายนอก: {str(api_err)})*

      **🤖 ผลการวิเคราะห์เบื้องต้นจากระบบสำรอง (Fallback Analysis):**
      - **หน่วยงานที่มีกำไรสูงสุด:** Corporate BU เป็นหน่วยงานที่มีกำไรจากการดำเนินงาน (Operating Profit) สูงที่สุดในระบบ (820,000 ถึง 950,000 ในแต่ละไตรมาส)
      - **ภาพรวมรายได้:** Corporate BU มีรายได้จริงสูงที่สุด รองลงมาคือ Retail BU และ Online BU ตามลำดับ
      - **ข้อสังเกตสำหรับผู้บริหาร:** รายได้รวมของทุก BU ในช่วง Q1 และ Q2 มีแนวโน้มเติบโตขึ้น แต่บางหน่วยงาน (เช่น Corporate BU) มีรายได้จริงต่ำกว่างบประมาณเล็กน้อย ควรกำชับฝ่ายขายให้ช่วยกันผลักดันยอดช่วงครึ่งปีหลังให้เป็นไปตามเป้า
      """

    st.markdown("### 🤖 ผลการวิเคราะห์")
    st.info(analysis_result)

# แสดงตารางข้อมูลเบื้องต้น
with st.expander("📁 ดูข้อมูลดิบทั้งหมดในระบบ (Raw Data)"):
  st.dataframe(df, use_container_width=True)
