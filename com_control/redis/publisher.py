import redis
import json
import logging
from typing import Any, Dict

class RedisPublisher:
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.logger = logging.getLogger(__name__)
        self.redis_client = redis.Redis(host=host, port=port)
        
    def publish_message(self, channel: str, message: Dict[str, Any]) -> bool:
        """发布消息到指定频道"""
        try:
            self.redis_client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            self.logger.error(f"消息发布失败: {str(e)}")
            return False 