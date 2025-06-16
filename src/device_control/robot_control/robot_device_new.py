from src.com_control.robot_com import RobotConnection
from src.uilt.logs_control.setup import device_control_logger
import threading
import time
import socket
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class RobotController:
    def __init__(self, mock):
        """
            机器人设备控制
            :param mock: 是否启用 Mock 模式
        """
        self.connection = RobotConnection(mock)

    def _execute_scenario(self, cmd_full, expected_response):
        """
        核心场景执行器（通用逻辑封装）
        :param command: 待发送的指令内容
        :param expected_response: 期望的响应内容
        :return: 布尔值（操作是否成功）
        """
        try:
            # 发送指令并记录操作
            self.connection.send_command(cmd_full)
            print(f"📤 Command Sent: {cmd_full}")

            self.connection.wait_for_response(cmd_full + "ok", 20)

            print("开始执行------")

            self.connection.wait_for_response(cmd_full + "_finish", 120)

            # # 等待预期响应并记录交互过程
            # device_control_logger.info(f"⏳ Waiting for: {expected_response}")
            # actual_response = self.wait_for_target(expected_response)

            # # 结果判定与日志输出
            # result = (actual_response == expected_response)
            # status = "✅ SUCCESS" if result else "❌ FAILURE"
            # device_control_logger.info(f"{status} ✅ {command} → {expected_response}")

            return True
        except Exception as e:
            device_control_logger.error(f"⚠️ Scenario Failed: {str(e)}")
            raise

    def install_column(self,column_id):
        """等待样本加载准备就绪
            传入参数的含义：
                第一位：取哪根色谱柱  1-6 顺时针
        """
        command = f"task_scara_zhuzi1_py({column_id})"
        return self._execute_scenario(command, "task_scara_zhuzi1_py_finish")

    def uninstall_column(self,column_id):
        command = f"task_scara_zhuzi2_py({column_id})"
        return self._execute_scenario(command, "Sample loading ready")

    def transfer_to_collect(self,position_id,sample_id):
        command = f"task_flask_move_py({position_id},1)"
        self._execute_scenario(command, f"task_flask_move_py({position_id},1)_finish")
        command = f"task_flask_move_py(17,0)"
        self._execute_scenario(command, "task_flask_move_py(17,0)_finish")
        command = f"task_scara_get_tool()"
        self._execute_scenario(command, "task_scara_get_tool()_finish")
        command = f"task_scara_sample_py({sample_id},1)"
        self._execute_scenario(command, f"task_scara_sample_py({sample_id},1)_finish")


    def to_clean_needle(self):
        command = f"sample_ok"
        self._execute_scenario(command, "sample_ok_finish")

        command = f"task_scara_clean_py(1)"
        self._execute_scenario(command, "Sample loading ready")

    def task_scara_put_tool(self):
        command = f"clean_ok"
        self._execute_scenario(command, "clean_ok_finish")


        command = f"task_scara_put_tool(1)"
        self._execute_scenario(command, "task_scara_put_tool(1)_finish")


    def collect_to_xuanzheng(self,bottle_id):
        command = f"task_flask_move_py(17,1)"
        self._execute_scenario(command, "task_flask_move_py(17,1)_finish")
        command = f"task_Rotary_Evaporator_put_py()"
        self._execute_scenario(command, "task_Rotary_Evaporator_put_py()_finish")

    def robot_to_home(self):
        command = f"Vacuum_ok"
        self._execute_scenario(command, "Vacuum_ok_finish")

    def transfer_to_clean(self):
        command = f"task_flask_move_py(15,0)"
        self._execute_scenario(command, "task_flask_move_py(15,0)_finish")

    def task_shake_the_flask_py(self):
        command = "task_shake_the_flask_py()"
        self._execute_scenario(command, "task_shake_the_flask_py()_finish")

    def get_penlin_needle(self):
        command = "task_abb_clean_py()"
        self._execute_scenario(command, "task_abb_clean_py()_finish")
        pass

    def abb_clean_ok(self):
        command = f"abb_clean_ok"
        self._execute_scenario(command, "abb_clean_ok_finish")

    def clean_to_home(self):
        command = f"task_flask_move_py(15,1)"
        self._execute_scenario(command, "task_flask_move_py(15,1)_finish")

    def get_transfer_needle(self):
        command = f"task_transfer_flask_liquid_py()"
        self._execute_scenario(command, "task_transfer_flask_liquid_py()_finish")

    def transfer_finish_flag(self):
        command = f"Liquid_transfer_ok"
        self._execute_scenario(command, "Liquid_transfer_ok_finish")

    def scara_to_home(self):
        command = f"task_scara_filling_liquid_ok()"
        self._execute_scenario(command, "task_scara_filling_liquid_ok()_finish")



    def clean_to_xuanzheng(self):
        command = f"task_flask_move_py(16,1)"
        self._execute_scenario(command, "task_flask_move_py(16,1)_finish")
        command = f"task_Rotary_Evaporator_put_py()"
        self._execute_scenario(command, "task_Rotary_Evaporator_put_py()_finish")
        pass

    def xuanzheng_to_warehouse(self, position_id):
        command = f"task_flask_move_py({position_id},0)"
        self._execute_scenario(command, f"task_flask_move_py({position_id},0)_finish")
        pass

    def get_xuanzheng(self):
        command = f"task_Rotary_Evaporator_get_py()"
        self._execute_scenario(command, "task_Rotary_Evaporator_get_py()_finish")

    def get_big_bottle(self, position_id):
        command = f"task_flask_move_py(15,1)"
        self._execute_scenario(command, "task_flask_move_py(15,1)_finish")
        command = f"task_flask_move_py({position_id},0)"
        self._execute_scenario(command, "task_flask_move_py(7,0)_finish")


    def small_big_to_clean(self,position_id):
        command = f"task_flask_move_py({position_id},1)"
        self._execute_scenario(command, f"task_flask_move_py({position_id},1)_finish")
        command = f"task_flask_move_py(16,0)"
        self._execute_scenario(command, "task_flask_move_py(16,0)_finish")


if __name__ == '__main__':
    pass
    controller = RobotController(mock=False)
    # controller.install_column(6)
    #
    # # 新增手动输入功能
    # def manual_input():
    #     """手动输入命令并验证响应"""
    #     command = input("请输入要发送的指令：")  # 第一步改为手动输入
    #     return controller.await_sample_loading_ready(command)
    #
    #
    #
    # # 核心工作流程（第一条为手动输入）
    # execution_flow = [
    #     manual_input,
    #     controller.trigger_clean_sequence,
    #     controller.proceed_to_evaporation_stage,
    #     controller.confirm_vacuum_prepared,
    #     controller.finalize_rotation_process,
    #     controller.reset_vacuum_system,
    #     controller.ready_clean,
    #     controller.input_numeric_command_2,
    #     controller.complete_transfer_process,
    #     controller.initiate_liquid_transfer,
    #
    #     controller.complete_transfer_process,
    #     controller.initiate_liquid_transfer,
    #
    #     controller.ready_liquid_transfer,
    #     controller.confirm_vacuum_prepared,
    #     controller.finalize_rotation_process,
    #     controller.finalize_last
    # ]
    #
    # results = {}
    # for step_idx, step_func in enumerate(execution_flow, 1):
    #     try:
    #         # 执行当前步骤
    #         result = step_func()
    #         results[f"Step {step_idx}"] = result
    #
    #         if not result:
    #             print(f"\n⚠️ 执行失败于步骤 {step_idx}")
    #             break
    #
    #     except Exception as e:
    #         print(f"\n⚠️ 步骤 {step_idx} 异常终止")
    #         print(f"错误详情: {str(e)}")
    #         results[f"Step {step_idx}"] = False
    #         break
    #
    # print("\nExecution Summary:")
    # for step, result in results.items():
    #     status = "✅ Passed" if result else "❌ Failed"
    #     print(f"{step}: {status}")