from src.device_control.sqlite.SQLiteDB import SQLiteDB

class MessageDB(SQLiteDB):
    """Inherit from SQLiteDB, specialized for storing Redis messages to messages table"""

    def __init__(self):
        super().__init__()
        self.table_name = "messages"
        self.init_table()

    def init_table(self):
        """Ensure messages table exists"""
        self.create_table(
            self.table_name,
            "id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP"
        )

    def write_to_db(self, message):
        """Store Redis messages in messages table"""
        columns = "content"
        self.insert_data(self.table_name, columns, [(message,)])
        print(f"[Database] Saved message: {message}")
db_messages = MessageDB()

if __name__ == "__main__":
    db = MessageDB()
    db.write_to_db("Test message from script")
