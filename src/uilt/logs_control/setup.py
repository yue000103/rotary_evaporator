import logging
from logging.config import dictConfig
import yaml
import os


def setup_logging(config_path="D:/project_python/rotary_evaporator/config/logging.yaml"):
    if config_path is None:
        base_path = os.path.dirname(__file__)
        config_path = os.path.join(base_path, '..', '..','..','..','config', 'logging.yaml')

    # print("config_path",config_path)
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)
        print(f"Warning: Logging configuration file not found. Using default logging level: INFO")


setup_logging()

# def get_logger(name):
#     return logging.getLogger(name)
# logger = logging.getLogger(__name__)
api_logger = logging.getLogger('api_log')
com_logger = logging.getLogger('com_log')
device_control_logger = logging.getLogger('device_control_log')
service_control_logger = logging.getLogger('service_control_log')
yaml_control_logger = logging.getLogger('yaml_control_log')
service_control_logger.debug("TEST: This is a debug log for service control.")



