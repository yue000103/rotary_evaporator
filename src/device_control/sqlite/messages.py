from src.device_control.sqlite.SQLiteDB import SQLiteDB

class MessageDB(SQLiteDB):
    """继承 SQLiteDB，专门用于存储 Redis 消息到 messages 表"""

    def __init__(self):
        super().__init__()  # 调用父类的初始化方法
        self.table_name = "messages"
        self.init_table()

    def init_table(self):
        """确保 messages 表存在"""
        self.create_table(
            self.table_name,
            "id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
        )

    def write_to_db(self, message):
        """将 Redis 消息存入 messages 表"""
        columns = "content"
        self.insert_data(self.table_name, columns, [(message,)])
        print(f"[Database] Saved message: {message}")
db_messages = MessageDB()

# 如果需要独立调用，也可以这样初始化
if __name__ == "__main__":
    db = MessageDB()
    db.write_to_db("Test message from script")
