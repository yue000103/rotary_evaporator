
import time



from src.device_control import (robot_controller,pump_sample,
                                xuanzheng_controller,pump_device,gear_pump,
                                inject_height)

from src.service_control.sepu.sepu_service import SepuService
sepu_api = SepuService()
column_id = 1
bottle_id = 1
wash_time_s = 10
experiment_time_min = 5
retain_tube = [{'module_id': 1, 'tube_list': [2, 3, 4]}]
clean_tube = [{'module_id': 1, 'tube_list': [1,2,3,4]}]
penlin_time_s = 3 * 1000


xuanzheng_controller.set_auto_set_height(True)
# 机器人放色谱柱（机器人、柱架）
robot_controller.install_column(column_id)


# 机器人取瓶子到收集架上
robot_controller.transfer_to_collect(bottle_id)

# # 色谱系统开始润柱
sepu_api.wash_column(wash_time_s)
#
# #色谱系统进样
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
#
# # 色谱终止实验
sepu_api.update_line_terminate()

# 降下收集针
inject_height.down_height()

# 收集
sepu_api.select_retain_tubes(retain_tube)

# 升起收集针
inject_height.up_height()

# 机械臂拿瓶子去旋蒸
robot_controller.collect_to_xuanzheng(bottle_id)


# 清洗
sepu_api.save_experiment_data(clean_tube)

# 旋蒸抽真空
xuanzheng_controller.run_vacuum()

# 机械臂挪走
robot_controller.robot_to_home()


#拿小瓶到清洗加
robot_controller.small_big_to_clean()

# 调节旋蒸高度
xuanzheng_controller.set_height(1000)

# 旋蒸开始
xuanzheng_controller.run_evaporation()

xuanzheng_controller.xuanzheng_sync()

# 等待旋蒸结束

# 调节旋蒸高度
xuanzheng_controller.set_height(0)

# 机械臂拿瓶子去清洗架
robot_controller.get_xuanzheng()
xuanzheng_controller.drain_valve_open()
robot_controller.robot_to_home()

robot_controller.transfer_to_clean()


# 喷淋

robot_controller.get_penlin_needle()

gear_pump.start_pump(penlin_time_s)

robot_controller.abb_clean_ok()


robot_controller.clean_to_home()

# 机械臂摇晃
robot_controller.task_shake_the_flask_py()


robot_controller.transfer_to_clean()

robot_controller.get_transfer_needle()

# 启动蠕动泵
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

# 拿小瓶去旋蒸
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


xuanzheng_controller.set_auto_set_height(False)


#健康空旋蒸







