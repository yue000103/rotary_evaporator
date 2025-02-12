import logging
from pathlib import Path
import yaml

def setup_logging():
    """配置日志系统"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
     # 添加文件处理器
    file_handler = logging.FileHandler(log_dir / "com" / "com.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger("com").addHandler(file_handler)
      
def load_config():
    """加载系统配置"""
    with open("config/system.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    setup_logging()
    config = load_config()
    logger = logging.getLogger("com")
    logger.info("机器人控制系统启动...")

if __name__ == "__main__":
    main() 