import airsim

import threading
import os
import time
from PIL import Image
import io


# 创建目录的函数
def create_directory(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)


# 获取第一视角视频并保存为JPG的函数
def capture_video(folder,client, drone_list,cam_id, duration=20, interval=0.1):
    start_time = time.time()
    count = 0
    while time.time() - start_time < duration:  # 持续拍照直到时间结束
        count = count + 1


        #获取无人机四个视角图片前时间戳
        current_time = time.time()  # 获取当前时间的时间戳
        print(f"获取无人机四个视角图片 前 时间戳: {current_time}")
        # # 获取压缩的PNG图像
        # responses = client.simGetImages([
        #     airsim.ImageRequest(cam_id, airsim.ImageType.Scene, False, True),  # 前置相机
        # ], vehicle_name=drone_list[0])
        #
        # camera_names = ["front", "right", "left", "back"]
        # for i, response in enumerate(responses):
        #
        #     if response is None or response.image_data_uint8 is None:
        #         print(f"未能获取 {camera_names[i]} 相机的图像")
        #     else:
        #         #将图像数据转换为PIL Image对象
        #         img_data = response.image_data_uint8
        #         img = Image.open(io.BytesIO(img_data))
        #
        #         # 如果图像是RGBA模式，转换为RGB模式
        #         if img.mode == 'RGBA':
        #             img = img.convert('RGB')
        #         print(f"{i},{camera_names[i]}")
        #         # 生成文件名
        #         image_filename = os.path.join(folder_list[0], f"{count}_{camera_names[i]}.jpg")
        #
        #         # 将图像保存为JPG文件
        #         img.save(image_filename, format="JPEG")
        response = client.simGetImages([
            airsim.ImageRequest(cam_id, airsim.ImageType.Scene, False, True),  # 前置相机
        ], vehicle_name=drone_list[0])[0]
        #将图像数据转换为PIL Image对象
        img_data = response.image_data_uint8
        img = Image.open(io.BytesIO(img_data))

        # 如果图像是RGBA模式，转换为RGB模式
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        # 生成文件名
        image_filename = os.path.join(folder, f"{count}_{cam_id}.jpg")

        # 将图像保存为JPG文件
        img.save(image_filename, format="JPEG")

        # 获取无人机四个视角图片后时间戳
        current_time = time.time()  # 获取当前时间的时间戳
        print(f"获取无人机四个视角图片 后 时间戳: {current_time}")


        if cam_id == 0:
            drone_state = client.simGetGroundTruthKinematics(vehicle_name='Drone0')
        elif cam_id == 1:
            drone_state = client.simGetGroundTruthKinematics(vehicle_name='Drone1')
        elif cam_id == 2:
            drone_state = client.simGetGroundTruthKinematics(vehicle_name='Drone2')
        elif cam_id == 4:
            drone_state = client.simGetGroundTruthKinematics(vehicle_name='Drone4')

        position = drone_state.position
        x, y, z = position.x_val, position.y_val, position.z_val
        print(f"位置编号{count} {cam_id}线程位置：X={x}, Y={y}, Z={z}")
        # for drone in drone_list:
        #     # 获取无人机的位置
        #     # drone_state = client.getMultirotorState(vehicle_name=drone)
        #     # position = drone_state.kinematics_estimated.position
        #     # x, y, z = position.x_val, position.y_val, position.z_val
        #
        #     drone_state = client.simGetGroundTruthKinematics(vehicle_name=drone)
        #     position = drone_state.position
        #     x, y, z = position.x_val, position.y_val, position.z_val
        #     print(f"位置编号{count}单独线程{drone}位置：X={x}, Y={y}, Z={z}")
        # # 获取无人机位置后时间戳
        # current_time = time.time()  # 获取当前时间的时间戳
        # print(f"获取无人机位置 后 时间戳: {current_time}")
        time.sleep(interval)  # 控制拍照间隔


# 无人机飞行路径的函数
def fly_drone(client, drone_name, folder_name, duration):
    print(f"无人机名：{drone_name}")
    client.confirmConnection()
    client.enableApiControl(True, vehicle_name=drone_name)
    client.armDisarm(True, vehicle_name=drone_name)

    # 起飞
    client.takeoffAsync(vehicle_name=drone_name).join()

    # 不同的飞行路径（可以根据需要调整）
    if drone_name == 'Drone': #中间相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
    elif drone_name == 'Drone0':  # 前侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(3, 0, -3, 1.5, vehicle_name=drone_name).join()
    elif drone_name == 'Drone1': #右侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, 3, -3, 1.5, vehicle_name=drone_name).join()
    elif drone_name == 'Drone2':#左侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, -3, -3, 1.5, vehicle_name=drone_name).join()
    elif drone_name == 'Drone4':#后侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(-3, 0, -3, 1.5, vehicle_name=drone_name).join()
    # #着陆
    # client.landAsync(vehicle_name=drone_name).join()
    # client.armDisarm(False, vehicle_name=drone_name)
    # client.enableApiControl(False, vehicle_name=drone_name)


# 多线程控制函数
def main():
    #获取无人机初始位置
    client = airsim.MultirotorClient()
    drone_state = client.simGetGroundTruthKinematics(vehicle_name='Drone0')
    position = drone_state.position
    x, y, z = position.x_val, position.y_val, position.z_val
    print(f"初始位置参考：X={x}, Y={y}, Z={z}")

    drone_names = ['Drone', 'Drone0', 'Drone1', 'Drone2', 'Drone4']  # 无人机名称
    folder_names = ['Drone_Folder', 'Drone0_Folder','Drone1_Folder','Drone2_Folder','Drone4_Folder']  # 视频存放文件夹
    cam_id = [0,1,2,4]
    duration = 30  # 视频捕获时长

    threads = []
    create_directory(folder_names[0])
    # 为每架无人机创建一个线程
    for i in range(len(drone_names)):
        thread = threading.Thread(target=fly_drone,
                                  args=(airsim.MultirotorClient(), drone_names[i], folder_names[i], duration))
        threads.append(thread)
        #thread.start()
    #创建拍摄线程
    for cam_idx in cam_id:
        video_thread = threading.Thread(target=capture_video, args=(folder_names[0],airsim.MultirotorClient(), drone_names,cam_idx))
        threads.append(video_thread)
        #video_thread.start()

    for thread in threads:
        thread.start()
    # 等待所有线程完成
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()