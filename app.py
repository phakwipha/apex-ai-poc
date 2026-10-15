import anthropic
import streamlit as st

st.title("🧪 API Diagnostic Test")

# เช็คว่ามี Key ใน Secrets ไหม
if "ANTHROPIC_API_KEY" not in st.secrets:
    st.error("❌ ไม่พบ ANTHROPIC_API_KEY ใน Streamlit Secrets")
else:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
    st.write(f"🔑 Key ที่ดึงได้: `{api_key[:8]}...{api_key[-4:]}`")

    # ทดสอบยิง API ตรงๆ
    try:
        client = anthropic.Anthropic(api_key=api_key)
        res = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        st.success("✅ เชื่อมต่อสำเร็จ! API Key และ Model ใช้งานได้ปกติ")
        st.write("Response จาก Claude:", res.content[0].text)
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาด: {e}")
