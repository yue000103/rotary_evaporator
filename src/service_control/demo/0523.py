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
retain_tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}]
clean_tube = [{'module_id': 1, 'tube_list': [1,5]}]
penlin_time_s = 5


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


async def xuanzheng_sync_until_finish(task_ctrl: TaskController):
    while True:
        await task_ctrl.wait_if_paused()
        result = xuanzheng_controller.get_process()
        print("旋蒸状态:", result)
        if result.get("globalStatus", {}).get("running") is False:
            break
        await asyncio.sleep(2)


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
retain_tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}]
clean_tube = [{'module_id': 1, 'tube_list': [1,5]}]
penlin_time_s = 5


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


async def xuanzheng_sync_until_finish(task_ctrl: TaskController):
    while True:
        await task_ctrl.wait_if_paused()
        result = xuanzheng_controller.get_process()
        print("旋蒸状态:", result)
        if result.get("globalStatus", {}).get("running") is False:
            break
        await asyncio.sleep(2)


async def run_lab(task_ctrl: TaskController):
    try:
        step_map = {
            1: lambda: (print("🧪 1. 开始实验"),
                        robot_controller.install_column(column_id),
                        robot_controller.transfer_to_collect(bottle_id)),

            2: lambda: (print("🧼 2. 润柱"),
                        sepu_api.wash_column(wash_time_s),
                        sepu_api.update_line_pause()),

            3: lambda: (print("💉 3. 进样"),
                        pump_sample.inject(2, 1, 3),
                        pump_sample.sync(),
                        robot_controller.to_clean_needle()),

            4: lambda: (print("🧼 4. 洗针"),
                        pump_sample.inject(5, 1, 3),
                        pump_sample.sync()),

            5: lambda: (print("🧪 5. 开始色谱实验"),
                        robot_controller.task_scara_put_tool(),
                        sepu_api.set_start_tube(1,1),
                        sepu_api.update_line_start(),
                        sepu_api.start_column(experiment_time_min),
                        sepu_api.update_line_terminate()),

            6: lambda: (print("⬇️ 6. 收集"),
                        inject_height.down_height(),
                        sepu_api.select_retain_tubes(retain_tube),
                        inject_height.up_height()),

            7: lambda: (print("🧪 7. 收集转移到旋蒸"),
                        robot_controller.collect_to_xuanzheng(bottle_id)),

            8: lambda: (print("💨 8. 旋蒸开始"),
                        xuanzheng_controller.vacuum_until_below_threshold(),
                        robot_controller.robot_to_home(),
                        asyncio.create_task(robot_controller.small_big_to_clean()),
                        xuanzheng_controller.set_height(1000),
                        xuanzheng_controller.run_evaporation(),
                        xuanzheng_controller.xuanzheng_sync(),
                        xuanzheng_controller.set_height(0)),

            9: lambda: (print("🤖 9. 旋蒸结束取瓶,并排出废液"),
                        robot_controller.get_xuanzheng(),
                        xuanzheng_controller.drain_until_above_threshold(),
                        robot_controller.robot_to_home(),
                        robot_controller.transfer_to_clean(),
                        asyncio.create_task(xuanzheng_controller.start_waste_liquid())),

            10: lambda: (print("🚿 10. 喷淋清洗"),
                         robot_controller.get_penlin_needle(),
                         gear_pump.start_pump(penlin_time_s),
                         robot_controller.abb_clean_ok(),
                         robot_controller.clean_to_home(),
                         robot_controller.task_shake_the_flask_py(),
                         robot_controller.transfer_to_clean()),

            11: lambda: (print("🧽 11. 清洗轮次"),
                         robot_controller.get_transfer_needle(),
                         pump_device.start_pump(),
                         robot_controller.transfer_finish_flag(),
                         robot_controller.get_penlin_needle(),
                         gear_pump.start_pump(penlin_time_s),
                         robot_controller.abb_clean_ok()),

            12: lambda: (print("🚚 12. 清洗完成，返回旋蒸"),
                         robot_controller.scara_to_home(),
                         robot_controller.clean_to_xuanzheng()),

            13: lambda: (print("💨 13. 再次旋蒸"),
                         xuanzheng_controller.vacuum_until_below_threshold(),
                         robot_controller.robot_to_home(),
                         xuanzheng_controller.set_height(50),
                         xuanzheng_controller.run_evaporation(),
                         xuanzheng_controller.xuanzheng_sync(),
                         xuanzheng_controller.set_height(0)),

            14: lambda: (print("📦 14. 入库操作"),
                         robot_controller.get_xuanzheng(),
                         xuanzheng_controller.drain_until_above_threshold(),
                         xuanzheng_controller.start_waste_liquid(),
                         robot_controller.robot_to_home(),
                         robot_controller.xuanzheng_to_warehouse(),
                         robot_controller.get_big_bottle(),
                         print("✅ 全部任务完成"))
        }

        current_step = 1
        while current_step <= len(step_map):
            await task_ctrl.wait_if_paused()
            print(f"\n🛑 当前暂停在第 {current_step} 步")

            # 获取用户指令
            cmd = input("👉 输入 next 继续，数字跳转，exit 退出: ").strip()
            if cmd.lower() == "exit":
                print("🚫 用户终止了任务")
                break
            elif cmd.isdigit():
                step = int(cmd)
                if step in step_map:
                    current_step = step
                else:
                    print("⚠️ 无效步骤号")
                    continue
            else:
                # 默认为 next
                pass

            # 执行该步骤
            try:
                result = step_map[current_step]()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                print(f"❌ 执行步骤 {current_step} 时发生错误:", e)

            current_step += 1

    except asyncio.CancelledError:
        print("⛔ 任务被终止")
        try:
            await asyncio.to_thread(gear_pump.stop_pump)
            await asyncio.to_thread(pump_device.stop_pump)
        except Exception as e:
            print("❗ 设备终止异常:", e)


async def main():
    task_ctrl = TaskController()
    task = asyncio.create_task(run_lab(task_ctrl))

    try:
        await task
    except asyncio.CancelledError:
        print("主任务取消完成")


if __name__ == "__main__":
    asyncio.run(main())


