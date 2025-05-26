import asyncio

from src.device_control import (
    robot_controller, pump_sample,
    xuanzheng_controller, pump_device, gear_pump,
    inject_height
)

from src.service_control.sepu.sepu_service import SepuService

# 初始化参数
sepu_api = SepuService()
column_id = 1
bottle_id = 1
wash_time_s = 10
experiment_time_min = 5
retain_tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}, {'module_id': 2, 'tube_list': [4, 5, 6, 7, 8, 9, 10]}]
clean_tube = [{'module_id': 1, 'tube_list': [1, 2, 3, 4]}]
penlin_time_s = 10


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


async def run_lab(task_ctrl: TaskController):
    try:
        await task_ctrl.wait_if_paused()
        print("开始实验 ------ ")
        robot_controller.install_column(column_id)
        robot_controller.transfer_to_collect(bottle_id)

        # # 色谱系统开始润柱
        sepu_api.wash_column(wash_time_s)

        #色谱系统进样
        sepu_api.update_line_pause()
        	# 进样器进样
        response = pump_sample.inject(8000, 1, 3)
        print(f"Inject Response: {response}")
        pump_sample.sync()

        robot_controller.to_clean_needle()

        # #洗针
        response = pump_sample.inject(8000, 1, 3)
        print(f"Inject Response: {response}")
        pump_sample.sync()

        robot_controller.task_scara_put_tool()

        # # 色谱系统开始实验
        sepu_api.update_line_start()
        sepu_api.start_column(experiment_time_min)

        # 色谱终止实验
        sepu_api.update_line_terminate()

        inject_height.down_height()

        # 收集
        sepu_api.select_retain_tubes(retain_tube)

        inject_height.up_height()

        robot_controller.collect_to_xuanzheng(bottle_id)

        # 清洗
        sepu_api.save_experiment_data(clean_tube)

        xuanzheng_controller.run_vacuum()
        robot_controller.robot_to_home()
        robot_controller.small_big_to_clean()
        xuanzheng_controller.set_height(1000)
        xuanzheng_controller.run_evaporation()
        xuanzheng_controller.xuanzheng_sync()
        xuanzheng_controller.set_height(0)

        robot_controller.get_xuanzheng()
        xuanzheng_controller.drain_valve_open()
        robot_controller.robot_to_home()
        robot_controller.transfer_to_clean()

        # 喷淋阶段
        await asyncio.gather(
            asyncio.to_thread(robot_controller.get_penlin_needle),
            asyncio.to_thread(gear_pump.start_pump, penlin_time_s),
        )

        robot_controller.abb_clean_ok()
        robot_controller.clean_to_home()
        robot_controller.task_shake_the_flask_py()
        robot_controller.transfer_to_clean()

        robot_controller.get_transfer_needle()
        pump_device.start_pump()
        robot_controller.transfer_finish_flag()

        # 第一次清洗
        robot_controller.get_penlin_needle()
        gear_pump.start_pump(penlin_time_s)
        robot_controller.abb_clean_ok()

        robot_controller.get_transfer_needle()
        pump_device.start_pump()
        robot_controller.transfer_finish_flag()

        # 第二次清洗
        robot_controller.get_penlin_needle()
        gear_pump.start_pump(penlin_time_s)
        robot_controller.abb_clean_ok()

        robot_controller.get_transfer_needle()
        pump_device.start_pump()
        robot_controller.transfer_finish_flag()

        robot_controller.scara_to_home()
        robot_controller.clean_to_xuanzheng()

        # 旋蒸抽真空
        xuanzheng_controller.run_vacuum()

        # 机械臂挪走
        robot_controller.robot_to_home()

        # 调节旋蒸高度
        xuanzheng_controller.set_height(50)

        # 旋蒸开始
        xuanzheng_controller.run_evaporation()
        xuanzheng_controller.xuanzheng_sync()

        # 等待旋蒸结束

        # 调节旋蒸高度
        xuanzheng_controller.set_height(0)

        # 机械臂拿瓶子去仓库
        robot_controller.get_xuanzheng()
        xuanzheng_controller.drain_valve_open()
        robot_controller.robot_to_home()

        robot_controller.xuanzheng_to_warehouse()
        robot_controller.get_big_bottle()

        print("✅ 全部任务完成")

    except asyncio.CancelledError:
        print("⛔ 任务被终止")


# 示例控制逻辑
async def main():
    task_ctrl = TaskController()
    task = asyncio.create_task(run_lab(task_ctrl))

    await asyncio.sleep(5)
    print("暂停中...")
    task_ctrl.pause()

    await asyncio.sleep(3)
    print("继续运行...")
    task_ctrl.resume()

    await asyncio.sleep(15)
    print("终止任务...")
    task_ctrl.stop()
    await asyncio.sleep(1)

    try:
        await task
    except asyncio.CancelledError:
        print("主任务取消完成")


if __name__ == "__main__":
    asyncio.run(main())
