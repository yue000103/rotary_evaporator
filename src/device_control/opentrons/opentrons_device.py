import time
from src.com_control.opentrons_com import OpentronsConnection
from src.util.logs_control.setup import device_control_logger

class OpentronsDevice:
    def __init__(self, mock=False):
        """
        Opentrons 设备控制类
        :param mock: 是否启用 Mock 模式
        """
        self.mock = mock
        self.ot_com = OpentronsConnection(mock=mock)
        self.run_id = None
        self.protocol_id = None

    def get_protocols(self):
        """ 查找现有所有的实验协议
        {
  "data": [
    {
      "id": "string",
      "createdAt": "2025-03-26T02:24:11.788Z",
      "files": [
        {
          "name": "string",
          "role": "main"
        }
      ],
      "protocolType": "json",
      "robotType": "OT-2 Standard",
      "metadata": {
        "additionalProp1": {}
      },
      "analyses": [
        "string"
      ],
      "analysisSummaries": [
        {
          "id": "string",
          "status": "pending",
          "runTimeParameters": [
            {
              "displayName": "string",
              "variableName": "string",
              "description": "string",
              "suffix": "string",
              "type": "int",
              "min": 0,
              "max": 0,
              "value": 0,
              "default": 0
            },
            {
              "displayName": "string",
              "variableName": "string",
              "description": "string",
              "suffix": "string",
              "type": "int",
              "min": 0,
              "max": 0,
              "value": 0,
              "default": 0,
              "choices": [
                {
                  "displayName": "string",
                  "value": 0
                }
              ]
            },
            {
              "displayName": "string",
              "variableName": "string",
              "description": "string",
              "suffix": "string",
              "type": "bool",
              "min": 0,
              "max": 0,
              "value": true,
              "default": true
            },
            {
              "displayName": "string",
              "variableName": "string",
              "description": "string",
              "suffix": "string",
              "type": "csv_file",
              "min": 0,
              "max": 0,
              "value": 0,
              "default": 0,
              "file": {
                "id": "string",
                "name": "string"
              }
            }
          ]
        }
      ],
      "key": "string",
      "protocolKind": "standard"
    }
  ],
  "meta": {
    "cursor": 0,
    "totalLength": 0
  }
}


        """

        return self.ot_com.get("/protocols")

    def get_runs(self):
        """
        获取所有实验运行信息，返回实验运行的列表，并找到 self.protocol_id 对应的 run_id
        """
        response = self.ot_com.get("/runs")
        if response and "data" in response:
            runs = response["data"]
            for run in runs:
                if run.get("protocolId") == self.protocol_id:
                    self.run_id = run.get("id")
                    break  # 找到匹配的 run_id 后退出循环
            return runs  # 返回所有运行的列表
        return []

    def start_run(self, protocol_id, labware_offsets=None, runtime_params=None, runtime_files=None):
        """ 运行指定的实验协议 """
        self.protocol_id = protocol_id
        data = {
            "data": {
                "protocolId": protocol_id,
                "labwareOffsets": labware_offsets if labware_offsets else [],
                "runTimeParameterValues": runtime_params if runtime_params else {},
                "runTimeParameterFiles": runtime_files if runtime_files else {}
            }
        }
        response = self.ot_com.post("/runs", data)
        if response:
            run_id = response.get("data", {}).get("id")
            if run_id:
                device_control_logger.info(f"Run started with ID: {run_id}")
                return run_id
        device_control_logger.error("Failed to start run")
        return None

    def pause_run(self, run_id):
        """ 暂停实验
        1. "play"
            功能：启动运行任务；若运行任务处于暂停状态，则恢复运行。
            使用场景：当你需要开始一个新的运行任务，或者在运行任务被暂停后想继续执行时使用。
        2. "pause"
            功能：暂停运行任务。
            使用场景：在运行任务执行过程中，遇到需要暂时中断操作的情况，比如检查实验设备状态、添加试剂等，可以使用此操作。
        3. "stop"
            功能：停止（取消）运行任务。
            使用场景：当运行任务出现严重错误、不再需要继续执行或者实验提前结束时，可使用该操作来终止任务。
        4. "resume-from-recovery"
            功能：在运行任务进入错误恢复模式后，恢复正常的协议执行。从最后一个命令执行后机器人所处的状态继续运行。
            使用场景：当运行任务因错误进入恢复模式，并且错误已解决，希望从当前状态继续执行协议时使用。
        5. "resume-from-recovery-assuming-false-positive"
            功能：在运行任务进入错误恢复模式后，恢复正常的协议执行。假定潜在的错误是误报。
            使用场景：当运行任务因错误进入恢复模式，但你认为错误是误判的情况下，使用此操作忽略该错误并继续执行协议。

        """

        data = {"data": {"actionType": "pause"}}
        if self.ot_com.post(f"/runs/{run_id}/actions", data):
            device_control_logger.info(f"Run {run_id} paused successfully.")
            return True
        device_control_logger.error("Failed to pause run")
        return False

    def resume_run(self, run_id):
        """ 继续实验 """
        data = {"data": {"actionType": "play"}}
        response = self.ot_com.post(f"/runs/{run_id}/actions", data)

        if response:
            device_control_logger.info(f"Run {run_id} resumed successfully.")
            return True
        else:
            device_control_logger.error(f"Failed to resume run {run_id}.")
            return False

    def stop_run(self, run_id):
        """ 急停实验 """
        data = {"data": {"actionType": "stop"}}
        if self.ot_com.post(f"/runs/{run_id}/actions", data):
            device_control_logger.info(f"Run {run_id} stopped successfully.")
            return True
        device_control_logger.error("Failed to stop run")
        return False

    def set_lights(self, state: bool):
        """ 开启或关闭 Opentrons 设备的灯光 """
        data = {"on": state}
        if self.ot_com.post("/robot/lights", data):
            device_control_logger.info(f"Lights turned {'on' if state else 'off'} successfully.")
            return True
        device_control_logger.error("Failed to toggle lights")
        return False

    def get_light_status(self):
        """ 查询灯光状态，返回 True（灯亮）或 False（灯灭） """
        response = self.ot_com.get("/robot/lights")
        if response and "on" in response:
            return response["on"]
        return False  # 默认认为灯是关闭的

    def get_run_errors(self):
        """ 查询指定运行的错误，返回错误的 ID 列表 """
        response = self.ot_com.get(f"/runs/{self.run_id}/commandErrors")
        if response and "data" in response:
            return [error["id"] for error in response["data"]]
        return []

    def close(self):
        """ 关闭设备连接 """
        self.ot_com.close()
        device_control_logger.info("Opentrons device connection closed.")

if __name__ == '__main__':
    ot_device = OpentronsDevice(mock=False)
    protocols = ot_device.get_protocols()
    if protocols:
        protocol_id = protocols[0]['id']
        run_id = ot_device.start_run(protocol_id)
        if run_id:
            time.sleep(5)
            ot_device.pause_run(run_id)
            time.sleep(5)
            ot_device.stop_run(run_id)
    ot_device.close()
