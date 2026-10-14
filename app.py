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

    # ใช้โมเดลตามที่ Google API แนะนำใน Error Message ล่าสุด
    model = genai.GenerativeModel("gemini-3.8-flash")

    response = model.generate_content(prompt)
    sql_query = response.text.strip().replace("```sql", "").replace("```", "")

    conn = sqlite3.connect("enterprise_poc.db")
    df_result = pd.read_sql_query(sql_query, conn)
    conn.close()

    return sql_query, df_result
