import requests
import json

# API URL
url = "http://localhost:5000/method/update/operate"

# 构建请求负载
payload = {
    "method": {
        "samplingTime": 5,
        "detectorWavelength": 258,
        "equilibrationColumn": 1,
        "speed": 100,
        "totalFlowRate": 10,
        "cleanList": [
            {
                "module_id": 2,
                "liquid_volume": 20,
                "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        ],
        "cleaningCount": 2,
        "cleaningSpeed": None,
        "drainSpeed": None,
        "isocratic": 0,
        "methodName": "12",
        "pressure": 1,
        "pumpA": None,
        "pumpB": None,
        "pumpList": [
            {"time": 0, "pumpB": 100, "pumpA": 0, "flowRate": 30},
            {"time": 1, "pumpB": 100, "pumpA": 0, "flowRate": 30},
            {"time": 2, "pumpB": 0, "pumpA": 100, "flowRate": 30},
            {"time": 3, "pumpB": 0, "pumpA": 100, "flowRate": 30},
            {"time": 4, "pumpB": 0, "pumpA": 100, "flowRate": 30},
            {'time': 5, "pumpB": 0, "pumpA": 100, "flowRate": 30},
        ],
        "retainList": [
            {
                "module_id": 1,
                "liquid_volume": 8,
                "tube_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            }
        ],
        "smiles": "4896",
    },
    "method_id": "97",

}

# 发送POST请求
response = requests.post(url, json=payload)

# 判断请求是否成功
if response.status_code == 200:
    print("API调用成功！返回的数据：")
    print(response.json())  # 打印返回的JSON数据
else:
    print(f"API调用失败！状态码：{response.status_code}, 错误信息：{response.text}")
