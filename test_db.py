from db_config import get_db_connection

try:
    conn = get_db_connection()
    print("✅ Database Connected Successfully!")
    conn.close()
except Exception as e:
    print("❌ Connection Failed!")
    print(e)