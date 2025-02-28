from src.device_control import xuanzheng_controller
import redis
from src.device_control.sqlite.messages import db_messages  # 继承 SQLiteDB 的类

# Redis 服务器配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_CHANNEL = "ipc_channel"  # 进程间通信的频道
REDIS_LIST = "ipc_list"  # 存储历史消息的列表



def consumer():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    # 订阅频道
    pubsub = r.pubsub()
    pubsub.subscribe(REDIS_CHANNEL)

    print("[Consumer] Listening for messages...")

    for message in pubsub.listen():
        if message["type"] == "message":
            msg_content = message["data"]
            print(f"[Consumer] Received: {msg_content}")
            if msg_content == "True" :

                start_xuanzheng_service()
                print("[SHOUJI] Received True")
            # 存入 SQLite
            db_messages.write_to_db(msg_content)

            # # 取出并删除 Redis list 中的数据（可选）
            # stored_msg = r.lpop(REDIS_LIST)
            # if stored_msg:
            #     print(f"[Consumer] Processed from list and saved: {stored_msg}")


def start_xuanzheng_service():
    print("设备信息：", xuanzheng_controller.get_info())

    # 更改设备参数
    heating = {"set": 30, "running": True}
    cooling = {"set": 10, "running": True}
    vacuum = {"set": 500, "vacuumValveOpen": True, "aerateValvePulse": False}
    rotation = {"set": 60, "running": True}
    lift = {"set": 0}
    # globalStatus = {"running": False}
    globalStatus = None

    response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum, rotation=rotation,
                                                   lift=lift, running=None)
    print("PUT请求响应：", response)

    xuanzheng_controller.close()

if __name__ == '__main__':
    consumer()