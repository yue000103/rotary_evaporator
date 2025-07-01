import asyncio
import datetime
import time
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

class TaskController:
    def __init__(self):
        self._pause = asyncio.Event()
        self._pause.set()
        self._stop = False

    async def wait_if_paused(self):
        await self._pause.wait()
        if self._stop:
            raise asyncio.CancelledError()

    def pause(self):
        self._pause.clear()

    def resume(self):
        self._pause.set()

    def stop(self):
        self._stop = True
        self._pause.set()


def wash_needle():
    pump_device.start_waste_liquid()
    time.sleep(10)
    pump_device.start_washing_liquid()
    response = pump_sample.send_command('A10000M2000A0M2000A10000M2000A0')
    pump_sample.sync()
    pump_device.start_waste_liquid()
    robot_controller.task_scara_put_tool()


k = 0


async def run_lab(task_ctrl: TaskController, params_1: dict,big_bottle_volume,small_bottle_volume,column_id,wash_time_min,
                  experiment_time_min,sample_id,penlin_time_s,peak_number,small_position_id,big_position_id,warehouse_id,
                  sample_volume, xuanzheng_timeout_min,solid_sample):
    try:
        await task_ctrl.wait_if_paused()


        print(f"{datetime.datetime.now()}初始化注射泵")

        task_pump_init = asyncio.create_task(asyncio.to_thread(pump_sample.initialization))
        sepu_api.sepu_api.update_prep_chrom_params(params_1)

        print(f"{datetime.datetime.now()}🧪 1. 开始实验")
        await asyncio.gather(task_pump_init)

        robot_controller.install_column(column_id)
        time.sleep(25)
        robot_controller.transfer_to_collect(big_position_id,sample_id)

        # if solid_sample is False:

        print(f"{datetime.datetime.now()}🧼 2. 润柱")
        task_wash_colum = asyncio.create_task(
            asyncio.to_thread(sepu_api.wash_column, wash_time_min, experiment_time_min))
        await asyncio.gather(task_wash_colum)

        print(f"{datetime.datetime.now()}💉 3. 进样")
        robot_controller.into_smaple(sample_id)
        response = pump_sample.inject(sample_volume, 1, 3)
        print(f"Inject Response: {response}")
        pump_sample.sync()
        task_start_washing_liquid = asyncio.create_task(asyncio.to_thread(pump_device.start_washing_liquid))
        robot_controller.to_clean_needle()

        print(f"{datetime.datetime.now()}🧼 4. 洗针")
        await asyncio.gather(task_start_washing_liquid)
        response = pump_sample.inject(2, 1, 3)
        print(f"Inject Response: {response}")
        pump_sample.sync()
        response = pump_sample.send_command('A10000M2000A0M2000A10000M2000A0')
        print(f"Inject Response: {response}")
        pump_sample.sync()
        wash_needle()


        print(f"{datetime.datetime.now()}🧪 5. 开始色谱实验")
        sepu_api.set_start_tube(1,1)
        sepu_api.start_column(experiment_time_min)
        sepu_api.update_line_terminate()


        print(f"{datetime.datetime.now()}⬇️ 6. 收集")
        inject_height.down_height()
        code = sepu_api.select_retain_tubes(peak_number)
        if code == 600:
            print("无峰出现，清空试管")
            sepu_clean = asyncio.create_task(asyncio.to_thread(sepu_api.save_experiment_data))
            await asyncio.gather(sepu_clean)
            robot_controller.uninstall_column(column_id)
            inject_height.up_height()
            robot_controller.collect_to_start(big_position_id)
            return
        inject_height.up_height()
        sepu_clean = asyncio.create_task(asyncio.to_thread(sepu_api.save_experiment_data))



        print(f"{datetime.datetime.now()}🧪 7. 收集转移到旋蒸")
        robot_controller.collect_to_xuanzheng(bottle_id)

        print(f"{datetime.datetime.now()}💨 8. 旋蒸开始")
        xuanzheng_controller.vacuum_until_below_threshold()
        robot_controller.robot_to_home()
        xuanzheng_controller.set_height(big_bottle_volume)
        xuanzheng_controller.run_evaporation()
        small_big_to_clean = asyncio.create_task(asyncio.to_thread(robot_controller.small_big_to_clean,small_position_id))

        xuanzheng_controller.xuanzheng_sync(xuanzheng_timeout_min)
        xuanzheng_controller.set_height(0)


        print(f"{datetime.datetime.now()}🤖 9. 旋蒸结束取瓶,并且排出废液")
        await asyncio.gather(small_big_to_clean)
        robot_controller.get_xuanzheng()
        time.sleep(1)
        xuanzheng_controller.drain_until_above_threshold()
        time.sleep(1)
        robot_controller.robot_to_home()
        time.sleep(1)
        xuanzheng_controller.start_waste_liquid()
        time.sleep(1)
        robot_controller.transfer_to_clean()

        print(f"{datetime.datetime.now()}🚿 10. 喷淋清洗")
        robot_controller.get_penlin_needle()
        time.sleep(1)

        gear_pump.start_pump(penlin_time_s)

        robot_controller.abb_clean_ok()
        time.sleep(1)

        robot_controller.clean_to_home()
        time.sleep(1)

        robot_controller.task_shake_the_flask_py()
        time.sleep(1)

        robot_controller.transfer_to_clean()

        if small_bottle_volume == 50:
            print(f"🧽 50ml瓶已装满，先进行旋蒸")
            robot_controller.get_transfer_needle()
            pump_device.start_pump()
            robot_controller.transfer_finish_flag()
            time.sleep(1)
            robot_controller.scara_to_home()
            time.sleep(1)
            robot_controller.clean_to_xuanzheng()
            xuanzheng_controller.vacuum_until_below_threshold()
            robot_controller.robot_to_home()
            xuanzheng_controller.set_height(small_bottle_volume)
            xuanzheng_controller.run_evaporation()
            xuanzheng_controller.xuanzheng_sync(xuanzheng_timeout_min)
            xuanzheng_controller.set_height(0)
            robot_controller.get_xuanzheng()
            time.sleep(1)
            xuanzheng_controller.start_waste_liquid()
            time.sleep(1)
            robot_controller.robot_to_home()
            time.sleep(1)
            robot_controller.small_put_clean()


        for i in range(2):
            print(f"🧽 11-{i+1}. 清洗轮次")
            robot_controller.get_transfer_needle()
            time.sleep(1)

            pump_device.start_pump()
            time.sleep(1)

            robot_controller.transfer_finish_flag()
            time.sleep(1)

            robot_controller.get_penlin_needle()
            time.sleep(1)
            gear_pump.start_pump(1)
            robot_controller.abb_clean_ok()

        robot_controller.get_transfer_needle()
        time.sleep(1)
        pump_device.start_pump()
        time.sleep(1)
        robot_controller.transfer_finish_flag()
        #
        print(f"{datetime.datetime.now()}🚚 12. 清洗完成，返回旋蒸")
        time.sleep(1)
        robot_controller.scara_to_home()
        time.sleep(1)
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
        robot_controller.get_big_bottle(big_position_id)
        robot_controller.uninstall_column(column_id)

        await asyncio.gather(sepu_clean)

        print(f"{datetime.datetime.now()}✅ 全部任务完成")

    except asyncio.CancelledError:
        print(f"{datetime.datetime.now()}⛔ 任务被终止")
        try:
            await asyncio.to_thread(gear_pump.stop_pump)
            await asyncio.to_thread(pump_device.stop_pump)
        except Exception as e:
            print(f"{datetime.datetime.now()}设备终止异常:", e)
    except Exception as e:
        raise e


async def main():
    # time.sleep(60)

    params_list = [

        {
            "params": {
                "start_ratio": 95,
                "end_ratio": 66,
                "n1_volumes": 2,
                "gradient_rate": 2.5,
                "peak_threshold": 0.1,
                "column_volume": 34,  # 真实柱体积
                "sg_window": 21,  # 增大平滑窗口，适应更宽的峰q
                "sg_order": 3,
                "baseline_window": 180,  # 增大基线窗口
                "k_factor": 20  # 调整阈值系数，提高检测灵敏度
            },
            "big_bottle_volume": 1000,
            "small_bottle_volume": 100,
            "column_id": 6,
            "wash_time_min": 5,
            "experiment_time_min": 20,
            "sample_id": 2,
            "sample_volume": 2,
            "penlin_time_s": 3,
            "peak_number": 1,
            "small_position_id": 1,
            "big_position_id": 7,
            "warehouse_id": 1,
            "xuanzheng_timeout_min": 20,
            "solid_sample": False  # 是否为固体样品

        },

        {
            "params": {
                "start_ratio": 100.0,
                "end_ratio": 90.0,
                "n1_volumes": 2.0,
                "gradient_rate": 0.6,
                "peak_threshold": 0.1,
                "column_volume": 35.0,
                "sg_window": 21,
                "sg_order": 3,
                "baseline_window": 180,
                "k_factor": 10.0
            },
            "big_bottle_volume": 1000,
            "small_bottle_volume": 100,
            "column_id": 5,
            "wash_time_min": 5,
            "experiment_time_min": 20,
            "sample_id": 3,
            "sample_volume": 2,
            "penlin_time_s": 3,
            "peak_number": 1,
            "small_position_id": 3,
            "big_position_id": 7,
            "warehouse_id": 3,
            "xuanzheng_timeout_min": 20,
            "solid_sample": False  # 是否为固体样品

        },

        {
            "params": {
                "start_ratio": 100.0,
                "end_ratio": 97.0,
                "n1_volumes": 2.0,
                "gradient_rate": 0.15,
                "peak_threshold": 0.1,
                "column_volume": 35.0,
                "sg_window": 21,
                "sg_order": 3,
                "baseline_window": 180,
                "k_factor": 10.0
            },
            "big_bottle_volume": 1000,
            "small_bottle_volume": 100,
            "column_id": 4,
            "wash_time_min": 5,
            "experiment_time_min": 20,
            "sample_id": 1,
            "sample_volume": 2,
            "penlin_time_s": 3,
            "peak_number": 1,
            "small_position_id": 2,
            "big_position_id": 7,
            "warehouse_id": 2,
            "xuanzheng_timeout_min":20,
            "solid_sample" : False  # 是否为固体样品
        },

    ]
    i = 0
    for params  in params_list:
        print(f"开始第{i+1}次实验")
        print(f"传入参数为{params}")
        task_ctrl = TaskController()
        await run_lab(task_ctrl=task_ctrl, params_1=params["params"],big_bottle_volume=params["big_bottle_volume"],small_bottle_volume=params["small_bottle_volume"]
                      ,column_id=params["column_id"],wash_time_min=params["wash_time_min"],experiment_time_min=params["experiment_time_min"]
                      ,sample_id=params["sample_id"],penlin_time_s=params["penlin_time_s"],peak_number=params["peak_number"],small_position_id=params["small_position_id"]
                      ,big_position_id=params["big_position_id"],warehouse_id=params["warehouse_id"],sample_volume= params["sample_volume"]
                      ,xuanzheng_timeout_min=params["xuanzheng_timeout_min"], solid_sample=params["solid_sample"])


if __name__ == "__main__":
    asyncio.run(main())
    # robot_controller.get_xuanzheng()
    # robot_controller.robot_to_home()
    # robot_controller.small_put_clean()



