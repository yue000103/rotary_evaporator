import redis
import json

class RedisSubscriber:
    def __init__(self):
        self.redis_conn = redis.Redis(
            host='127.0.0.1',  # 替换为你的 Redis 地址
            port=6379,
            db=0,
            decode_responses=True
        )
        self.pubsub = self.redis_conn.pubsub()

    def subscribe_channel(self, channel_name: str):
        """订阅指定频道并持续监听消息"""
        self.pubsub.subscribe(channel_name)
        print(f"开始监听频道：{channel_name}...")

        try:
            for message in self.pubsub.listen():
                if message["type"] == "message":
                    # 解析 JSON 格式的消息内容
                    data = json.loads(message["data"])
                    print(f"收到新命令: {data}")
                    # 在这里添加你的业务逻辑（如触发机器人动作）
                    
        except KeyboardInterrupt:
            print("\n手动停止监听")
        except Exception as e:
            print(f"监听异常: {str(e)}")
        finally:
            self.pubsub.close()

if __name__ == '__main__':
    subscriber = RedisSubscriber()
    subscriber.subscribe_channel("ROBOT_COMMAND_CHANNEL")  # 与你发布的频道名一致