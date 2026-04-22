import redis
from src.device_control.sqlite.messages import db_messages

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_CHANNEL = "ipc_channel"
REDIS_LIST = "ipc_list"

def consumer():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)

    print("[Consumer] Listening for messages...")

    for message in pubsub.listen():
        if message["type"] == "message":
            msg_content = message["data"]
            print(f"[Consumer] Received: {msg_content}")

            db_messages.write_to_db(msg_content)

            stored_msg = r.lpop(REDIS_LIST)
            if stored_msg:
                print(f"[Consumer] Processed from list and saved: {stored_msg}")

if __name__ == "__main__":
    consumer()
