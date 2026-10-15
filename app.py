import google.generativeai as genai
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
        <p style='color: #4b5563; font-size: 16px;'>ระบบรายงานผู้บริหารและผู้ช่วยวิเคราะห์ข้อมูลอัตโนมัติ (Gemini 3.8 Flash)</p>
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

# ตรวจสอบการตั้งค่า API Key ใน Streamlit Secrets
if "GEMINI_API_KEY" not in st.secrets:
  st.error("❌ กรุณาตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets ให้เรียบร้อย")
  st.stop()

# ตั้งค่าการใช้งาน Gemini API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# ล็อกชื่อรุ่นตามที่ API Error บังคับมา ห้ามเปลี่ยนเป็นชื่ออื่นอีกเด็ดขาด
MODEL_NAME = "gemini-3.8-flash"

# ส่วนช่องพิมพ์คำถามแชทแบบอิสระ
st.markdown("### 💬 พูดคุยและสอบถามข้อมูลการเงินกับ AI")
user_question = st.text_input(
    "พิมพ์คำถามหรือสิ่งที่คุณต้องการวิเคราะห์จากข้อมูลการเงิน:",
    placeholder="เช่น เปรียบเทียบรายได้ Retail BU กับ Online BU หรือ BU ไหนทำกำไรสูงสุด",
)

col1, col2 = st.columns([1, 5])
with col1:
  analyze_btn = st.button("ส่งคำถาม", type="primary")

if analyze_btn:
  if not user_question.strip():
    st.warning("⚠️ กรุณากรอกคำถามที่ต้องการวิเคราะห์ก่อนครับ")
  else:
    with st.spinner("กำลังประมวลผลคำตอบ..."):
      try:
        model = genai.GenerativeModel(MODEL_NAME)
        data_summary = df.to_string(index=False)
        prompt = f"""
                คุณคือผู้ช่วยผู้บริหารด้านการเงิน วิเคราะห์ข้อมูล P&L ต่อไปนี้เพื่อตอบคำถามของผู้ใช้
                
                คำถามของผู้ใช้: "{user_question}"
                
                ข้อมูลตาราง pnl_data:
                {data_summary}
                
                กรุณาตอบเป็นภาษาไทย กระชับ ชัดเจน และตรงไปตรงมาสำหรับผู้บริหาร
                """

        response = model.generate_content(prompt)
        st.markdown("### 🤖 ผลลัพธ์จากการวิเคราะห์")
        st.info(response.text)
      except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการประมวลผลจาก AI: {e}")

# แสดงตารางข้อมูลเบื้องต้น
with st.expander("📁 ดูข้อมูลดิบทั้งหมดในระบบ (Raw Data)"):
  st.dataframe(df, use_container_width=True)
