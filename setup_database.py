from core.database import init_database, create_tables
from config import DATABASE_CONFIG

def setup_db():
    """独立执行：初始化数据库并创建所有表结构"""
    conn = init_database(DATABASE_CONFIG)
    if conn:
        create_tables(conn)
        print("数据库表结构创建完成！")
        conn.close()

if __name__ == "__main__":
    setup_db()