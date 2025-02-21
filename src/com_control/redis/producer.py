import redis
import time

# Redis 服务器配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_CHANNEL = "ipc_channel"  # 进程间通信的频道
REDIS_LIST = "ipc_list"  # 存储历史消息的列表


def producer():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    count = 200
    while True:
        message = f"Message {count} from Producer"

        # 1. 发布到频道（pub/sub）
        r.publish(REDIS_CHANNEL, message)

        # 2. 存入 Redis list（持久化）
        r.rpush(REDIS_LIST, message)

        print(f"[Producer] Sent: {message}")
        count += 1
        time.sleep(2)  # 模拟数据间隔


if __name__ == "__main__":
    producer()
