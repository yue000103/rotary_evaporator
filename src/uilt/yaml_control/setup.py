import yaml
import os
from src.uilt.logs_control.setup import yaml_control_logger


# 获取当前脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
# print("script_dir",script_dir)
config_path = os.path.join(script_dir, '../../../config/com_config.yaml')
# print("--------------",config_path)

# 读取 `com_config.yaml`
def load_config():
    if not os.path.exists(config_path):
        yaml_control_logger.warning(f"Config file not found: {config_path}. Using default values.")
        return {}  # 返回空字典，避免 `NoneType` 问题

    with open(config_path, "r", encoding="utf-8") as file:
        try:
            return yaml.safe_load(file) or {}  # 避免返回 `None`
        except yaml.YAMLError as e:
            yaml_control_logger.error(f"Error loading YAML config: {e}")
            return {}  # 解析失败，返回空字典

config = load_config()

def get_base_url(key="default"):
    """ 获取指定 `key` 对应的 `base_url`，如果不存在则使用 `default` """
    # print(config)
    base_urls = config.get("base_urls", {})  # 获取所有 `base_urls`
    # print("base_urls1",base_urls)
    base_url = base_urls.get(key, base_urls.get("xuanzheng", "192.168.1.20"))
    # print("base_url2",base_url)
    return base_url  # 优先使用 `key`，否则使用 `default`

