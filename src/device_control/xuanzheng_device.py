import time

from src.com_control.xuanzheng_com import ConnectionController
from src.com_control import plc
import json
import signal
import os
import threading
from datetime import datetime

from contextlib import contextmanager


@contextmanager
def timeout(seconds):
    """超时上下文管理器"""

    def timeout_handler(signum, frame):
        raise TimeoutError(f"操作超时 ({seconds}秒)")

    # 设置信号处理
    old_handler = signal.signal(signal.SIGABRT, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGABRT, old_handler)





class XuanZHengController:
    def __init__(self,mock=False):
        self.connection = ConnectionController(mock)
        self.plc = plc
        self.plc.mock = mock  # 设置 PLC 通信是否为 Mock 模式
        self.HEIGHT_ADDRESS = 502
        self.AUTO_SET = 500
        self.AUTO_FINISH = 501
        self.WASTE_LIQUID = 323
        self.WASTE_LIQUID_FINISH = 333
        self.mock = mock






    def get_info(self):
        return self.connection.send_request("/api/v1/info", method='GET')

    def get_process(self):
        return self.connection.send_request("/api/v1/process", method='GET')

    def start_collect(self, interval=1, save_dir="data_log"):
        """阻塞式采集 get_process 数据，Ctrl+C 或进程结束时写入 txt 文件"""
        os.makedirs(save_dir, exist_ok=True)
        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
        filepath = os.path.join(save_dir, filename)
        buffer = []

        print(f"数据采集已启动，保存路径: {filepath}（Ctrl+C 结束）")
        try:
            while True:
                try:
                    data = self.get_process()
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    buffer.append(f"[{ts}] {data}")
                except Exception as e:
                    print(f"采集异常: {e}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("收到结束信号，正在保存...")
        finally:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(buffer))
            print(f"采集已停止，共 {len(buffer)} 条，保存至: {filepath}")
            return filepath

    def start_collect_with_plot(self, interval=1, save_dir="data_log",
                                signals=("vacuum", "heating", "cooling", "rotation"),
                                max_points=300, save_fig=True):
        """实时采集并绘制信号曲线。关闭窗口或 Ctrl+C 结束，自动保存数据与图片。

        signals: 要绘制的字段名（取 result[field]['act']）
        max_points: 图中最多展示的最近数据点数
        """
        import matplotlib.pyplot as plt
        from collections import deque

        os.makedirs(save_dir, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(save_dir, stamp + ".txt")
        png_path = os.path.join(save_dir, stamp + ".png")

        buffer = []
        times = deque(maxlen=max_points)
        series = {s: deque(maxlen=max_points) for s in signals}

        plt.ion()
        fig, ax = plt.subplots(figsize=(10, 5))
        lines = {s: ax.plot([], [], label=s)[0] for s in signals}
        ax.set_xlabel("time (s)")
        ax.set_ylabel("act value")
        ax.set_title("XuanZheng realtime signals")
        ax.legend(loc="upper right")
        ax.grid(True)

        closed = {"flag": False}
        fig.canvas.mpl_connect("close_event", lambda e: closed.update(flag=True))

        t0 = time.time()
        print(f"实时绘图采集启动，数据: {txt_path}，图片: {png_path}（Ctrl+C 或关闭窗口结束）")
        try:
            while not closed["flag"]:
                try:
                    raw = self.get_process()
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    buffer.append(f"[{ts}] {raw}")

                    if isinstance(raw, str):
                        result = json.loads(raw) if raw.strip() else {}
                    else:
                        result = raw or {}

                    t = time.time() - t0
                    times.append(t)
                    for s in signals:
                        val = result.get(s, {}).get("act")
                        series[s].append(val if isinstance(val, (int, float)) else float("nan"))
                        lines[s].set_data(list(times), list(series[s]))

                    ax.relim()
                    ax.autoscale_view()
                    fig.canvas.draw_idle()
                    fig.canvas.flush_events()
                except Exception as e:
                    print(f"采集/绘图异常: {e}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("收到结束信号，正在保存...")
        finally:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(buffer))
            if save_fig:
                try:
                    fig.savefig(png_path, dpi=150, bbox_inches="tight")
                except Exception as e:
                    print(f"图片保存失败: {e}")
            plt.ioff()
            plt.close(fig)
            print(f"采集已停止，共 {len(buffer)} 条，数据: {txt_path}，图片: {png_path}")
            return txt_path, png_path

    def xuanzheng_sync(self, timeout_min=2):
        """轮询获取旋蒸当前状态，等待其先运行再结束"""

        has_started = False  # 标志位：是否检测到旋蒸运行开始
        timeout = timeout_min * 60
        start_time = time.time()
        try:
            while True:
                if time.time() - start_time > timeout:
                    print(f"⏰ 超过超时时间 {timeout_min} 分钟，退出轮询。")
                    self.stop_evaporation()
                    break
                raw_result = self.get_process()
                print("当前状态：", raw_result)

                # 判断数据格式
                if isinstance(raw_result, str):
                    try:
                        result = json.loads(raw_result)
                    except json.JSONDecodeError as e:
                        print(f"JSON 解析失败: {e}")
                        break
                elif isinstance(raw_result, dict):
                    result = raw_result
                else:
                    print("未知的返回类型，既不是 str 也不是 dict，退出")
                    break

                is_running = result.get("globalStatus", {}).get("running", False)

                if is_running:
                    print("设备正在运行...")
                    has_started = True  # 标记设备已经开始运行
                elif has_started:
                    print("检测到运行结束，退出轮询。")
                    break
                else:
                    print("尚未开始运行，继续等待...")

                time.sleep(2)

        except Exception as e:
            print(f"xuanzheng_sync 轮询过程中发生异常: {e}")
        finally:
            print("结束执行 xuanzheng_sync 函数")

    def change_device_parameters(self, heating=None, cooling=None, vacuum=None, rotation=None, lift=None, running=None,
                                 program=None):
        data = {}

        if heating is not None:
            data["heating"] = {
                "set": heating["set"],
                "running": heating.get("running", False)
            }

        if cooling is not None:
            data["cooling"] = {
                "set": cooling["set"],
                "running": cooling.get("running", False)
            }

        if vacuum is not None:
            data["vacuum"] = {
                "set": vacuum["set"],
                "vacuumValveOpen": vacuum.get("vacuumValveOpen", False),
                "aerateValveOpen": vacuum.get("aerateValveOpen", False),
                "aerateValvePulse": vacuum.get("aerateValvePulse", False)
            }

        if rotation is not None:
            data["rotation"] = {
                "set": rotation["set"],
                "running": rotation.get("running", True)
            }

        if lift is not None:
            data["lift"] = {"set": lift["set"]}

        if running is not None:
            data["globalStatus"] = {"running": running}

        if program is not None:
            data["program"] = {
                "type": program.get("type", "AutoDest"),
                "endVacuum": program.get("endVacuum", 0),
                "flaskSize": program.get("flaskSize", 2)
            }

        return self.connection.send_request("/api/v1/process", method='PUT', data=data)

    def close(self):
        self.connection.close()




    def set_height(self,volume):
        #1000 500 100 50
        if volume == 1000:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1050)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 2}
            )

        elif volume == 500:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1150)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 1}
            )
        elif volume == 100:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1400)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 1}
            )
        elif volume == 50:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 1417)
            self.change_device_parameters(
                program={"type": "AutoDest", "flaskSize": 1}
            )
        elif volume == 0:
            self.plc.write_single_register(self.HEIGHT_ADDRESS, 0)
        time.sleep(1)

        self.plc.write_coil(self.AUTO_SET,True)


        time.sleep(3)
        self.height_finish_async()
        time.sleep(1)
        self.plc.write_coil(self.AUTO_SET,False)



    def set_auto_set_height(self,flag:bool):
        self.plc.write_coil(self.AUTO_SET,flag)

    def height_finish_async(self):
        while True:
            print("-----------height_finish_async----------")
            done = self.plc.read_coils(self.AUTO_FINISH,1)[0]
            time.sleep(2)
            if done:
                return True
    def start_waste_liquid(self):
        print("start waste_liquid")
        self.plc.write_coil(self.WASTE_LIQUID, True)
        time.sleep(1)
        self.plc.write_coil(self.WASTE_LIQUID, False)
        time.sleep(2)
        print("-----stop--------------waste_liquid---------------------------")
        # self.waste_finish_async()

    def start_waste_liquid_with_timeout(self, timeout_seconds=10):
        """带超时的废液启动方法"""
        start_time = time.time()
        try:
            # 原来的操作
            self.start_waste_liquid()

            # 检查是否超时
            if time.time() - start_time > timeout_seconds:
                raise TimeoutError(f"废液启动超时: {timeout_seconds}秒")

            return True
        except Exception as e:
            print(f"废液启动失败: {e}")
            return False

    def waste_finish_async(self):
        while True:
            done = self.plc.read_coils(self.WASTE_LIQUID_FINISH)[0]
            # print(done)
            if done:
                return True
            time.sleep(1)


        # pass
        # self.plc.write_coil(self.HEIGHT_ADDRESS, True)

    # def set_height_up(self):
    #     # self.plc.write_single_register(self.HEIGHT_ADDRESS, height)
    #     self.plc.write_coil(self.HEIGHT_ADDRESS, False)

        #307

    def run_vacuum(self):
        heating = None
        cooling = None
        vacuum = {"set": 150, "vacuumValveOpen": True, "aerateValveOpen": False}
        rotation = None
        lift = {"set": 0}
        globalStatus = None

        response = self.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=None)
        print("PUT请求响应：", response)

    def stop_vacuum(self):
        heating = None
        cooling = None
        vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": False}
        rotation = None
        lift = {"set": 0}
        globalStatus = None

        response = self.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
                                                                 rotation=rotation,
                                                                 lift=lift, running=None)
        print("PUT请求响应：", response)

    def run_evaporation(self):
        running = True
        # globalStatus = None

        response = self.change_device_parameters(heating=None, cooling=None, vacuum=None,
                                                                  rotation=None,
                                                                 lift=None, running=running)
        time.sleep(10)

        print("PUT请求响应：", response)


    def stop_evaporation(self):
        running = False
        # globalStatus = None

        response = self.change_device_parameters(heating=None, cooling=None, vacuum=None,
                                                                 rotation=None,
                                                                 lift=None, running=running)
        print("PUT请求响应：", response)

    def drain_valve_open(self):
        vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": True, "aerateValvePulse": False}

        # globalStatus = None

        response = self.change_device_parameters(heating=None, cooling=None, vacuum=vacuum,
                                                                 rotation=None,
                                                                 lift=None, running=None)
        print("PUT请求响应：", response)
        time.sleep(5)

    def vacuum_until_below_threshold(self, threshold=400):
        """
        启动抽真空，直到 vacuum.act 小于阈值（默认400）后停止。
        """
        if self.mock:
            print(f"✅ 真空值已低于 {threshold}，停止抽真空")

            return
        print("🌀 开始抽真空")
        self.run_vacuum()

        while True:
            raw_result = self.get_process()
            result = json.loads(raw_result) if isinstance(raw_result, str) else raw_result

            act = result.get("vacuum", {}).get("act", 9999)
            print(f"当前真空值: {act:.1f} mbar")

            if act < threshold:
                print(f"✅ 真空值已低于 {threshold}，停止抽真空")
                self.stop_vacuum()
                break

            time.sleep(1)

    def drain_until_above_threshold(self, threshold=900):
        """
        打开排气阀，直到 vacuum.act 大于阈值（默认900）后等待5秒。
        """
        if self.mock:
            print(f"✅ 真空值已高于 {threshold}，等待 5 秒")

            return
        print("💨 打开排气阀")
        self.drain_valve_open()

        while True:
            raw_result = self.get_process()

            # 增加空字符串判断
            if isinstance(raw_result, str):
                if not raw_result.strip():
                    # 可以选择抛出异常或返回默认值
                    result = {}  # 或者 result = {}
                else:
                    result = json.loads(raw_result)
            else:
                result = raw_result

            act = result.get("vacuum", {}).get("act", 0)
            print(f"当前真空值: {act:.1f} mbar")

            if act > threshold:
                print(f"✅ 真空值已高于 {threshold}，等待 5 秒")
                time.sleep(5)
                break

            time.sleep(1)

    def test_1(self):
        print("test_1 start")
        time.sleep(5)
        print("test_1 end")

    def test_2(self):
        print("test_2 start")
        time.sleep(10)
        print("test_2 end")
    def test_3(self):
        print("test_3 start")
        time.sleep(3)
        print("test_3 end")

    def test_4(self):
        print("test_4 start")
        time.sleep(3)
        print("test_4 end")


# 使用示例
if __name__ == "__main__":

    # 直接初始化 ProcessController，可选择 mock 模式
    controller = XuanZHengController(mock=False)  # mock=True 开启模拟模式
    controller.start_collect_with_plot()
    # controller.set_height(0)

    # controller.get_info()
    # controller.
    # controller.xuanzheng_sync()

    # 获取信息（模拟模式下不会真正发送请求）
    # print("设备信息：", controller.get_process())

    # controller.change_device_parameters(
    #     program={"type": "AutoDest", "flaskSize": 1}
    # )
    # 隔个1分钟get一次
    # controller.set_height(0)

    # # 更改设备参数
    # heating = {"set": 30, "running": False}
    # cooling = {"set": 10, "running": False}
    # vacuum = {"set": 500, "vacuumValveOpen": False, "aerateValveOpen": True,"aerateValvePulse":True}
    # # rotation = {"set": 60, "running": False}
    # lift = {"set": 0}
    # globalStatus = {"running": True}

    # heating = None
    # cooling = None
    # vacuum = {"set": 150, "vacuumValveOpen": False, "aerateValveOpen": False}
    # rotation = None
    # lift = {"set": 0}
    # globalStatus = None

    # response = xuanzheng_controller.change_device_parameters(heating=heating, cooling=cooling, vacuum=vacuum,
    #                                                          rotation=rotation,
    #                                                          lift=lift, running=None)
    # globalStatus = None
    #
    # response = controller.change_device_parameters(heating=None, cooling=None, vacuum=vacuum, rotation=None,
    #                                                lift=None,running=False)
    # print("PUT请求响应：", response)

    # controller.close()
    # controller.waste_finish_async()
    # controller.run_vacuum()
    # controller.set_height(100)
    # controller.run_evaporation()
    # controller.xuanzheng_sync()
    # controller.set_height(0)
    # controller.vacuum_until_below_threshold()
    # controller.start_waste_liquid()

    # controller.set_auto_set_height(True)
    #
    # controller.set_height(0)
    # print("----------------")