import datetime
import time
import threading
from concurrent.futures import ThreadPoolExecutor

from humanfriendly.terminal import ansi_width
#from scipy.special import kwargs

from src.device_control import (
    robot_controller, pump_sample,
    xuanzheng_controller, pump_device, gear_pump,
    inject_height
)

from src.service_control.sepu.sepu_service import SepuService

params_1 = {
    "start_ratio": 100.0,
    "end_ratio": 95.0,
    "n1_volumes": 2.0,
    "gradient_rate": 0.2,
    "peak_threshold": 0.1,
    "column_volume": 34.0,
    "sg_window": 21,
    "sg_order": 3,
    "baseline_window": 180,
    "k_factor": 10.0
}

params_2 = {
    "start_ratio": 100.0,
    "end_ratio": 95.0,
    "n1_volumes": 2.0,
    "gradient_rate": 0.2,
    "peak_threshold": 0.1,
    "column_volume": 34.0,
    "sg_window": 21,
    "sg_order": 3,
    "baseline_window": 180,
    "k_factor": 10.0
}

# 初始化参数
sepu_api = SepuService()
column_id = 6
bottle_id = 1
experiment_time_min = 5
wash_time_min = 1

penlin_time_s = 3
small_bottle_volume = 100
big_bottle_volume = 1000
sample_id = 1
peak_number = 1
global_warehouse_id = 1
global_small_position_id = 1

class TaskController:
    def __init__(self):
        self._pause = threading.Event()
        self._pause.set()
        self._stop = False
        self._lock = threading.Lock()

    def wait_if_paused(self):
        self._pause.wait()
        if self._stop:
            raise Exception("TaskCancelled")

    def pause(self):
        with self._lock:
            self._pause.clear()

    def resume(self):
        with self._lock:
            self._pause.set()

    def stop(self):
        with self._lock:
            self._stop = True
            self._pause.set()


def wash_needle():
    pump_device.start_waste_liquid()
    time.sleep(3)
    pump_device.start_washing_liquid()
    response = pump_sample.send_command('A10000M2000A0M2000A10000M2000A0')
    pump_sample.sync()
    pump_device.start_waste_liquid()
    robot_controller.task_scara_put_tool()




def start_experiment(task_ctrl: TaskController, params_1: dict, big_bottle_volume, small_bottle_volume, column_id,
                     wash_time_min, experiment_time_min, sample_id, penlin_time_s, peak_number, small_position_id,
                     big_position_id, warehouse_id, sample_volume, xuanzheng_timeout_min,solid_sample):
    print(f"{datetime.datetime.now()}初始化注射泵")

    # 使用线程池并行执行注射泵初始化和色谱参数设置
    with ThreadPoolExecutor(max_workers=2) as executor:
        pump_future = executor.submit(pump_sample.initialization)
        sepu_future = executor.submit(sepu_api.sepu_api.update_prep_chrom_params, params_1)

        # 等待两个任务完成
        pump_future.result()
        sepu_future.result()

    print(f"{datetime.datetime.now()}🧪 1. 开始实验")
    robot_controller.install_column(column_id)
    time.sleep(20)
    robot_controller.transfer_to_collect(big_position_id, sample_id)


    if solid_sample is True:
        return
    # 使用线程池并行执行洗柱和机器人操作
    with ThreadPoolExecutor(max_workers=2) as executor:
        wash_future = executor.submit(sepu_api.wash_column, wash_time_min, experiment_time_min)

        print(f"{datetime.datetime.now()}🧼 2. 润柱")
        wash_future.result()

    print(f"{datetime.datetime.now()}💉 3. 进样")
    robot_controller.into_smaple(sample_id)
    response = pump_sample.inject(sample_volume, 1, 3)
    print(f"Inject Response: {response}")
    pump_sample.sync()

    robot_controller.to_clean_needle()
    pump_device.start_washing_liquid()

    print(f"{datetime.datetime.now()}🧼 4. 洗针")
    response = pump_sample.inject(2, 1, 3)
    print(f"Inject Response: {response}")
    pump_sample.sync()

    wash_needle_thread = threading.Thread(target=wash_needle)
    wash_needle_thread.start()
    wash_needle_thread.join()




def start_in_collect(experiment_time_min):

    print(f"{datetime.datetime.now()}🧼 2. 润柱")

    sepu_api.wash_column(0.2, experiment_time_min)

    print(f"{datetime.datetime.now()}🧪 5. 开始色谱实验")
    sepu_api.set_start_tube(1, 1)
    sepu_api.start_column(experiment_time_min)
    sepu_api.update_line_terminate()

def small_to_xuanzhegn(task_ctrl: TaskController, params_1: dict, big_bottle_volume, small_bottle_volume, column_id,
                       wash_time_min, experiment_time_min, sample_id, penlin_time_s, peak_number, small_position_id,
                       big_position_id, warehouse_id, sample_volume, xuanzheng_timeout_min):

    print(f"{datetime.datetime.now()}🚚 12. 清洗完成，返回旋蒸")
    robot_controller.clean_to_xuanzheng()

    print(f"{datetime.datetime.now()}💨 13. 再次旋蒸")
    xuanzheng_controller.vacuum_until_below_threshold()
    robot_controller.robot_to_home()

    xuanzheng_controller.set_height(small_bottle_volume)
    xuanzheng_controller.run_evaporation()
    xuanzheng_controller.xuanzheng_sync(xuanzheng_timeout_min)
    xuanzheng_controller.set_height(0)

    print(f"{datetime.datetime.now()}📦 14. 入库操作")
    robot_controller.get_xuanzheng()
    xuanzheng_controller.drain_until_above_threshold()
    xuanzheng_controller.start_waste_liquid()

    robot_controller.robot_to_home()
    robot_controller.xuanzheng_to_warehouse(warehouse_id)
    global global_warehouse_id
    global_warehouse_id = global_warehouse_id +1


def big_to_xuanzheng(task_ctrl: TaskController, params_1: dict, big_bottle_volume, small_bottle_volume, column_id,
                     wash_time_min, experiment_time_min, sample_id, penlin_time_s, peak_number, small_position_id,
                     big_position_id, warehouse_id, sample_volume, xuanzheng_timeout_min):
    print(f"{datetime.datetime.now()}🧪 7. 收集转移到旋蒸")
    robot_controller.collect_to_xuanzheng(bottle_id)

    print(f"{datetime.datetime.now()}💨 8. 旋蒸开始")
    xuanzheng_controller.vacuum_until_below_threshold()
    robot_controller.robot_to_home()
    xuanzheng_controller.set_height(big_bottle_volume)
    xuanzheng_controller.run_evaporation()
    global global_small_position_id
    global_small_position_id = global_small_position_id + 1
    # 把小瓶放到清洗架上
    clean_thread = threading.Thread(target=robot_controller.small_big_to_clean, args=(small_position_id,))
    clean_thread.start()

    xuanzheng_controller.xuanzheng_sync(xuanzheng_timeout_min)
    xuanzheng_controller.set_height(0)

    print(f"{datetime.datetime.now()}🤖 9. 旋蒸结束取瓶,并且排出废液")
    clean_thread.join()  # 等待清洗完成
    robot_controller.get_xuanzheng()
    xuanzheng_controller.drain_until_above_threshold()
    robot_controller.robot_to_home()
    xuanzheng_controller.start_waste_liquid()


def clean_and_transfer(task_ctrl: TaskController, params_1: dict, big_bottle_volume, small_bottle_volume, column_id,
                       wash_time_min, experiment_time_min, sample_id, penlin_time_s, peak_number, small_position_id,
                       big_position_id, warehouse_id, sample_volume, xuanzheng_timeout_min):
    print(f"{datetime.datetime.now()}🚿 10. 喷淋清洗")
    robot_controller.transfer_to_clean()
    robot_controller.get_penlin_needle()
    time.sleep(1)

    gear_pump.start_pump(penlin_time_s)

    robot_controller.abb_clean_ok()
    robot_controller.clean_to_home()
    robot_controller.task_shake_the_flask_py()
    robot_controller.transfer_to_clean()

    if small_bottle_volume == 50:
        print(f"🧽 50ml瓶已装满，先进行旋蒸")
        robot_controller.get_transfer_needle()
        pump_device.start_pump()
        robot_controller.transfer_finish_flag()

        robot_controller.scara_to_home()
        robot_controller.clean_to_xuanzheng()
        xuanzheng_controller.vacuum_until_below_threshold()
        robot_controller.robot_to_home()
        xuanzheng_controller.set_height(small_bottle_volume)
        xuanzheng_controller.run_evaporation()
        xuanzheng_controller.xuanzheng_sync(xuanzheng_timeout_min)
        xuanzheng_controller.set_height(0)
        xuanzheng_controller.start_waste_liquid()
        robot_controller.get_xuanzheng()
        robot_controller.robot_to_home()
        robot_controller.small_put_clean()

    for i in range(2):
        print(f"🧽 11-{i + 1}. 清洗轮次")
        robot_controller.get_transfer_needle()
        pump_device.start_pump()
        robot_controller.transfer_finish_flag()

        robot_controller.get_penlin_needle()
        time.sleep(1)
        gear_pump.start_pump(1)
        robot_controller.abb_clean_ok()

    robot_controller.get_transfer_needle()
    pump_device.start_pump()
    robot_controller.transfer_finish_flag()
    robot_controller.scara_to_home()



def collect(task_ctrl: TaskController, params_1: dict, big_bottle_volume, small_bottle_volume, column_id,
            wash_time_min, experiment_time_min, sample_id, penlin_time_s, peak_number, small_position_id,
            big_position_id, warehouse_id, sample_volume, xuanzheng_timeout_min):
    try:
        task_ctrl.wait_if_paused()

        print(f"{datetime.datetime.now()}⬇️ 6. 收集")
        inject_height.down_height()


        code = sepu_api.select_retain_tubes(peak_number)
        if code == 600:
            print("无峰出现，清空试管")
            save_experiment_data_thread = threading.Thread(target=sepu_api.save_experiment_data)
            save_experiment_data_thread.start()
            robot_controller.uninstall_column(column_id)
            inject_height.up_height()
            robot_controller.collect_to_start(big_position_id)
            save_experiment_data_thread.join()
            return 600
        inject_height.up_height()

        print(f"{datetime.datetime.now()}✅ 全部任务完成")

    except Exception as e:
        print(f"{datetime.datetime.now()}⛔ 任务被终止")
        try:
            pass
        except Exception as e:
            print(f"{datetime.datetime.now()}设备终止异常:", e)
        raise e


def main():
    task_ctrl = TaskController()

    params = {
        "params": {
            "start_ratio": 80,
            "end_ratio": 20,
            "n1_volumes": 2,
            "gradient_rate": 0.5,
            "peak_threshold": 0.1,
            "column_volume": 57,  # 真实柱体积
            "sg_window": 21,  # 增大平滑窗口，适应更宽的峰q
            "sg_order": 3,
            "baseline_window": 180,  # 增大基线窗口
            "k_factor": 20  # 调整阈值系数，提高检测灵敏度
        },
        "big_bottle_volume": 1000,
        "small_bottle_volume": 100,
        "column_id": 1,
        "wash_time_min": 0.2,
        "experiment_time_min": 15,
        "sample_id": 5,
        "sample_volume": 15,
        "penlin_time_s": 3,
        "peak_number": 3,
        "small_position_id": 1,
        "big_position_id": 7,
        "warehouse_id": 1,
        "xuanzheng_timeout_min": 20,
        "solid_sample": True  # 是否为固体样品
    }
    start_experiment(task_ctrl=task_ctrl, params_1=params["params"],
                     big_bottle_volume=params["big_bottle_volume"],
                     small_bottle_volume=params["small_bottle_volume"],
                     column_id=params["column_id"], wash_time_min=params["wash_time_min"],
                     experiment_time_min=params["experiment_time_min"],
                     sample_id=params["sample_id"], penlin_time_s=params["penlin_time_s"],
                     peak_number=params["peak_number"], small_position_id=params["small_position_id"],
                     big_position_id=params["big_position_id"], warehouse_id=params["warehouse_id"],
                     sample_volume=params["sample_volume"],
                     xuanzheng_timeout_min=params["xuanzheng_timeout_min"],
                     solid_sample=params["solid_sample"])

    PEAKS_NUM = 0
    SMALL_NUM = 6
    loop_num = 0
    peaks_num = 0
    global global_warehouse_id, global_small_position_id
    global_small_position_id = params["small_position_id"]
    global_warehouse_id = params["warehouse_id"]
    j = 0
    while input("是否继续实验？(y/n): ").strip().lower() == 'y':
        j = j + 1
        print(f"开始第{j}个循环 ---------- {datetime.datetime.now()}")

        start_in_collect(params["experiment_time_min"])
        print("get_detected_peaks:",sepu_api.get_detected_peaks())
        peaks_num = sepu_api.get_peaks_num() - peaks_num
        print("当前检测到的峰数:", peaks_num)
        peaks_num = int(input("请输入峰的数量（peaks_num）："))

        small_to_xuanzhegn_thread = None

        for i in range(peaks_num):

            PEAKS_NUM = PEAKS_NUM + 1
            if PEAKS_NUM > SMALL_NUM:
                loop_num = loop_num + 1
                print(f"检测到峰数 {PEAKS_NUM} 已达到小瓶旋蒸上限 {SMALL_NUM}，请复位所有小瓶，")
                PEAKS_NUM = 0
                global_small_position_id = params["small_position_id"]
                global_warehouse_id = params["warehouse_id"]
                input("按enter继续执行")
            print("当前小瓶位置:", global_small_position_id)
            print("当前产物位置:", global_warehouse_id)
            peak_number = i + 1  # 假设峰编号从1开始

            args = dict(
                task_ctrl=task_ctrl,
                params_1=params["params"],
                big_bottle_volume=params["big_bottle_volume"],
                small_bottle_volume=params["small_bottle_volume"],
                column_id=params["column_id"],
                wash_time_min=params["wash_time_min"],
                experiment_time_min=params["experiment_time_min"],
                sample_id=params["sample_id"],
                penlin_time_s=params["penlin_time_s"],
                peak_number=peak_number,
                small_position_id=global_small_position_id,
                big_position_id=params["big_position_id"],
                warehouse_id=global_warehouse_id,
                sample_volume=params["sample_volume"],
                xuanzheng_timeout_min=params["xuanzheng_timeout_min"]
            )

            print(f"开始收集{peak_number}个峰 ---------- {datetime.datetime.now()}")

            if i == 0:

                collect(**args)


                big_to_xuanzheng(**args)
                clean_and_transfer(**args)
                if i == peaks_num - 1:
                    break
                robot_controller.clean_to_collect()
            elif i == peaks_num - 1:
                small_to_xuanzhegn_thread = threading.Thread(target=small_to_xuanzhegn, kwargs=args)
                small_to_xuanzhegn_thread.start()

                collect(**args)
                    # 等待前一个小瓶旋蒸任务完成
                if small_to_xuanzhegn_thread:
                    small_to_xuanzhegn_thread.join()
                big_to_xuanzheng(**args)
                clean_and_transfer(**args)

                break
            else:
                # 创建线程执行小瓶旋蒸任务
                small_to_xuanzhegn_thread = threading.Thread(target=small_to_xuanzhegn, kwargs=args)
                small_to_xuanzhegn_thread.start()
                collect(**args)

                # 等待前一个小瓶旋蒸任务完成
                if small_to_xuanzhegn_thread:
                    small_to_xuanzhegn_thread.join()
                big_to_xuanzheng(**args)
                clean_and_transfer(**args)
                robot_controller.clean_to_collect()

        if peaks_num != 0:
            args = dict(
                task_ctrl=task_ctrl,
                params_1=params["params"],
                big_bottle_volume=params["big_bottle_volume"],
                small_bottle_volume=params["small_bottle_volume"],
                column_id=params["column_id"],
                wash_time_min=params["wash_time_min"],
                experiment_time_min=params["experiment_time_min"],
                sample_id=params["sample_id"],
                penlin_time_s=params["penlin_time_s"],
                peak_number=peaks_num,
                small_position_id=global_small_position_id,
                big_position_id=params["big_position_id"],
                warehouse_id=global_warehouse_id,
                sample_volume=params["sample_volume"],
                xuanzheng_timeout_min=params["xuanzheng_timeout_min"]
            )

            # # 创建线程执行小瓶旋蒸任务
            small_to_xuanzhegn_thread = threading.Thread(target=small_to_xuanzhegn, kwargs=args)
            small_to_xuanzhegn_thread.start()

        # 启动数据保存线程
        sepu_clean_thread = threading.Thread(target=sepu_api.save_experiment_data)
        sepu_clean_thread.start()

        # 等待小瓶旋蒸任务完成
        if small_to_xuanzhegn_thread:
            small_to_xuanzhegn_thread.join()
            robot_controller.clean_to_collect()

        if peaks_num == 0:
            # robot_controller.collect_to_start(params["big_position_id"])
            print("没有峰被检测到，跳过小瓶旋蒸任务。")

        # 等待数据保存完成
        sepu_clean_thread.join()

    print(f"一共有{PEAKS_NUM}个峰被检测到，实验结束。")
    robot_controller.collect_to_start(params["big_position_id"])
    robot_controller.uninstall_column(params["column_id"])

if __name__ == "__main__":
    main()