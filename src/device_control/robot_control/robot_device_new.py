from src.com_control.robot_com import RobotConnection
from src.uilt.logs_control.setup import device_control_logger
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class RobotController:
    def __init__(self, mock=False):
        """
            机器人设备控制
            :param mock: 是否启用 Mock 模式
        """
        self.connection = RobotConnection(mock)


    def _execute_scenario(self, command, expected_response):
        """
        核心场景执行器（通用逻辑封装）
        :param command: 待发送的指令内容
        :param expected_response: 期望的响应内容
        :return: 布尔值（操作是否成功）
        """
        try:
            # 发送指令并记录操作
            self.connection.send_command(command)
            device_control_logger.info(f"📤 Command Sent: {command}")

            # 等待预期响应并记录交互过程
            device_control_logger.info(f"⏳ Waiting for: {expected_response}")
            actual_response = self.connection.wait_for_target(expected_response)

            # 结果判定与日志输出
            result = (actual_response == expected_response)
            status = "✅ SUCCESS" if result else "❌ FAILURE"
            device_control_logger.info(f"{status} ✅ {command} → {expected_response}")

            return result
        except Exception as e:
            device_control_logger.error(f"⚠️ Scenario Failed: {str(e)}")
            return False

    def await_sample_loading_ready(self,command):
        """等待样本加载准备就绪
            传入参数的含义：
                第一位：取哪根色谱柱  1-6 顺时针
                第二位：上样瓶  1-9
                第三位：大瓶的位置  1，2
                第四位：小瓶的位置 1-6
        """
        return self._execute_scenario(command, "Sample loading ready")

    def trigger_clean_sequence(self):
        """触发清洁流程初始化"""
        return self._execute_scenario("sample_ok", "clean ready")

    def proceed_to_evaporation_stage(self):
        """推进至旋转蒸发阶段"""
        return self._execute_scenario("clean_ok", "ABB Reached Rotary Evaporator")

    def confirm_vacuum_prepared(self):
        """确认真空系统就绪"""
        return self._execute_scenario("Vacuum_ok", "wait_pc")

    def finalize_rotation_process(self):
        """完成旋转蒸发流程"""
        return self._execute_scenario("Rotary evaporation completed", "wait_pc")



    def reset_vacuum_system(self):
        """重置真空系统状态"""
        return self._execute_scenario("Vacuum reset", "clean ready")

    def ready_clean(self):
        """完成旋转蒸发流程"""
        return self._execute_scenario("clean_ok", "wait_pc")

    def input_numeric_command_2(self):
        """输入数值指令3"""
        return self._execute_scenario("2", "Liquid transfer ready")

    def reconfirm_vacuum_reset(self):
        """二次确认真空重置状态"""
        return self._execute_scenario("Vacuum reset", "clean ready")

    def initiate_liquid_transfer(self):
        """启动液体转移流程"""
        return self._execute_scenario("clean_ok", "Liquid transfer ready")

    def complete_transfer_process(self):
        """完成液体转移闭环"""
        return self._execute_scenario("Liquid transfer ok", "clean ready")

    def ready_liquid_transfer(self):
        """完成液体转移闭环"""
        return self._execute_scenario("Liquid transfer ok", "ABB Reached Rotary Evaporator")

    def revert_to_loading_state(self):
        """恢复至样本加载初始状态"""
        return self._execute_scenario("clean_ok", "Sample loading ready")

    def finalize_last(self):
        """完成完整清洁工作循环"""
        return self._execute_scenario("Vacuum reset", "finish")

    def validate_empty_command_flow(self):
        """验证空指令序列的稳定性"""
        return self._execute_scenario("", "Sample loading ready")


if __name__ == '__main__':
    controller = RobotController(mock=False)

    # 新增手动输入功能
    def manual_input():
        """手动输入命令并验证响应"""
        command = input("请输入要发送的指令：")  # 第一步改为手动输入
        return controller.await_sample_loading_ready(command)



    # 核心工作流程（第一条为手动输入）
    execution_flow = [
        manual_input,
        controller.trigger_clean_sequence,
        controller.proceed_to_evaporation_stage,
        controller.confirm_vacuum_prepared,
        controller.finalize_rotation_process,
        controller.reset_vacuum_system,
        controller.ready_clean,
        controller.input_numeric_command_2,
        controller.complete_transfer_process,
        controller.initiate_liquid_transfer,

        controller.complete_transfer_process,
        controller.initiate_liquid_transfer,

        controller.ready_liquid_transfer,
        controller.confirm_vacuum_prepared,
        controller.finalize_rotation_process,
        controller.finalize_last
    ]

    results = {}
    for step_idx, step_func in enumerate(execution_flow, 1):
        try:
            # 执行当前步骤
            result = step_func()
            results[f"Step {step_idx}"] = result

            if not result:
                print(f"\n⚠️ 执行失败于步骤 {step_idx}")
                break

        except Exception as e:
            print(f"\n⚠️ 步骤 {step_idx} 异常终止")
            print(f"错误详情: {str(e)}")
            results[f"Step {step_idx}"] = False
            break

    print("\nExecution Summary:")
    for step, result in results.items():
        status = "✅ Passed" if result else "❌ Failed"
        print(f"{step}: {status}")