import redis
import time

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_CHANNEL = "ipc_channel"
REDIS_LIST = "ipc_list"


def producer():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    count = 200
    while True:
        message = f"True"

        r.publish(REDIS_CHANNEL, message)

        r.rpush(REDIS_LIST, message)

        print(f"[Producer] Sent: {message}")
        count += 1
        time.sleep(2)


if __name__ == "__main__":
    producer()
