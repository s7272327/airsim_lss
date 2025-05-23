
import airsim
import threading
import os
import time
from PIL import Image
import io
import shutil
from collections import namedtuple
import json
import uuid
import pickle
import random

#################这里记录数据集中的场景##################
#"downtown_west_0"
#"downtown_west_1"
#"downtown_west_2"


scene_name = "downtown_west_2"


DroneState = namedtuple("DroneState", ["timestamp", "x", "y", "z", "qx", "qy", "qz", "qw"])
drones_states: list[list[DroneState]] =[]


# 创建目录的函数
def create_directory(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def delete_directory(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

# 获取无人机0四个视角的图像和对应时刻其他无人机的位置信息
def capture_data(client, drone_list, duration=20, interval=0.5):
    start_time = time.time()
    for _ in drone_list:
        drone_states = []
        drones_states.append(drone_states)
    count = 0
    while time.time() - start_time < duration:  # 持续拍照直到时间结束

        current_time = time.time()  # 获取当前时间的时间戳

        for i, drone in enumerate(drone_list):
            #获取无人机位置、姿态信息
            #根据名字区分无人机
            drone_state = client.simGetGroundTruthKinematics(vehicle_name=drone)
            #位置估计
            position = drone_state.position
            curr_x, curr_y, curr_z = position.x_val, position.y_val, position.z_val

            #这里应该有位置修正函数，以补充相机拍摄时间导致的位置偏移

            #姿态估计
            orientation = drone_state.orientation
            curr_qx, curr_qy, curr_qz, curr_qw = orientation.x_val, orientation.y_val, orientation.z_val, orientation.w_val

            #这里四个无人机使用统一的时间戳（都使用循环开始时的时间，循环获取位置时间可忽略不计），为了后面token检索方便
            state_temp = DroneState(timestamp=current_time, x=curr_x, y=curr_y, z=curr_z, qx=curr_qx, qy=curr_qy, qz=curr_qz, qw=curr_qw)
            drones_states[i].append(state_temp)

            print(f"{count}时刻{drone}位置：X={curr_x}, Y={curr_y}, Z={curr_z}")
            # print(f"角度（四元数）{orientation}")
        count = count + 1
        time.sleep(interval)  # 控制拍照间隔
# 无人机飞行路径的函数
def fly_drone(client, drone_name):
    print("进入fly_drone函数")
    client.confirmConnection()
    client.enableApiControl(True, vehicle_name=drone_name)
    client.armDisarm(True, vehicle_name=drone_name)

    # 起飞
    client.takeoffAsync(vehicle_name=drone_name).join()

    # # 不同的飞行路径（可以根据需要调整）
    # # downtown_west_0
    # if drone_name == 'Drone0':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone1':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(2, 0, -3, 1, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone2':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(0, 2, -3, 1, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone3':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(0, -2, -3, 1, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone4':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(-2, 0, -3, 1, vehicle_name=drone_name).join()

    #downtown_west_1
    # if drone_name == 'Drone0':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(40, 0, -3, 2, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone1':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(40, 0, -3, 2, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone2':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(40, 0, -3, 2, vehicle_name=drone_name).join()
    # elif drone_name == 'Drone3':
    #     client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    #     client.moveToPositionAsync(40, 0, -3, 2, vehicle_name=drone_name).join()

    #downtown_west_2
    n_cycles = 10
    delay = 0.2
    dir = 0
    # 1) 为每架机配置专属的起点和终点
    if drone_name == 'Drone0':
        start = (0,  0, -3)
        end   = (0, 3, -3)
    elif drone_name == 'Drone1':
        start = (0,  0, -3)
        end   = (0, 3, -3)
        dir = 1
    elif drone_name == 'Drone2':
        start = (0, 0, -3)
        end   = (0, 3, -3)
        dir = 1
    else:
        # 如果是未知名字，直接返回
        return

    # 2) 往返循环
    for i in range(n_cycles):
        # 偶数次飞向 end，奇数次飞回 start
        if dir == 0:
            target = end if (i % 2 == 0) else start
        if dir == 1:
            target = end if (i % 2 == 1) else start
        # （可选）给速度加点小随机
        speed = random.uniform(1.5, 2.5)

        # 下发飞行命令并等待完成
        client.moveToPositionAsync(*target, speed, vehicle_name=drone_name).join()

        # 短暂停留一下，保证动作切换清晰
        time.sleep(delay)


# 多线程控制函数
def main():
    # —— 1. 读取 settings.json —— #
  settings_path = os.path.expanduser("C:/Users/sxk72/Documents/AirSim/settings.json")  # 改成实际路径


  with open(settings_path, "r") as f:
    cfg = json.load(f)

  vehicles = cfg.get("Vehicles", {})
  # drone_names 从 JSON 的 key 自动生成,替代原来的
  # drone_names = ['Drone0', 'Drone1', 'Drone2','Drone3']
  drone_names = list(vehicles.keys())
  #获取无人机初始位置
  client = airsim.MultirotorClient()
  drone_state = client.simGetGroundTruthKinematics(vehicle_name='Drone0')
  position = drone_state.position
  x, y, z = position.x_val, position.y_val, position.z_val
  print(f"初始位置参考：X={x}, Y={y}, Z={z}")


  #创建线程
  threads = []
  # 为每架无人机创建飞行线程
  for i in range(len(drone_names)):
      thread = threading.Thread(target=fly_drone,
                                args=(airsim.MultirotorClient(), drone_names[i]))
      threads.append(thread)
      thread.start()
  #创建数据采集线程
  data_thread = threading.Thread(target=capture_data, args=(airsim.MultirotorClient(), drone_names))
  threads.append(data_thread)
  data_thread.start()
  # 等待所有线程完成
  for thread in threads:
      thread.join()

  #将无人机飞行信息存储起来，之后调整settings.json文件为无重力模式，然后在另一文件中把无人机摆在指定位置上
  with open(f"drones_states_{scene_name}.pkl", "wb") as f:
      pickle.dump(drones_states, f)



if __name__ == "__main__":
  main()