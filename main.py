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
def capture_video(client, drone_name, folder_name, duration=10):
    create_directory(folder_name)
    start_time = time.time()

    while time.time() - start_time < duration:
        # 获取压缩的PNG图像
        responses = client.simGetImages([airsim.ImageRequest("0", airsim.ImageType.Scene, False, True)],
                                        vehicle_name=drone_name)
        response = responses[0]

        # 将图像数据转换为PIL Image对象
        img_data = response.image_data_uint8
        img = Image.open(io.BytesIO(img_data))

        # 如果图像是RGBA模式，转换为RGB模式
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # 生成文件名
        image_filename = os.path.join(folder_name, f"{drone_name}_{time.time():.6f}.jpg")

        # 将图像保存为JPG文件
        img.save(image_filename, format="JPEG")

        # 控制帧率
        time.sleep(0.1)


# 无人机飞行路径的函数
def fly_drone(client, drone_name, folder_name, duration):
    client.confirmConnection()
    client.enableApiControl(True, vehicle_name=drone_name)
    client.armDisarm(True, vehicle_name=drone_name)

    # 起飞
    client.takeoffAsync(vehicle_name=drone_name).join()

    # 不同的飞行路径（可以根据需要调整）
    if drone_name == 'Drone1':
        client.moveToPositionAsync(10, 0, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(10, 10, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, 10, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, 0, -10, 5, vehicle_name=drone_name).join()
    elif drone_name == 'Drone2':
        client.moveToPositionAsync(-10, 0, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(-10, -10, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, -10, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, 0, -10, 5, vehicle_name=drone_name).join()
    elif drone_name == 'Drone3':
        client.moveToPositionAsync(5, 5, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(-5, 5, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(-5, -5, -10, 5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(5, -5, -10, 5, vehicle_name=drone_name).join()

    # 开始捕获视频
    capture_video(client, drone_name, folder_name, duration)

    # 着陆
    client.landAsync(vehicle_name=drone_name).join()
    client.armDisarm(False, vehicle_name=drone_name)
    client.enableApiControl(False, vehicle_name=drone_name)


# 多线程控制函数
def main():
    drone_names = ['Drone1', 'Drone2', 'Drone3']  # 无人机名称
    folder_names = ['Drone1_Folder', 'Drone2_Folder', 'Drone3_Folder']  # 视频存放文件夹
    duration = 10  # 视频捕获时长

    threads = []

    # 为每架无人机创建一个线程
    for i in range(len(drone_names)):
        thread = threading.Thread(target=fly_drone,
                                  args=(airsim.MultirotorClient(), drone_names[i], folder_names[i], duration))
        threads.append(thread)
        thread.start()
    # 创建拍摄线程
    video_thread = threading.Thread(target=capture_video, args=(client, drone_name, folder_name, duration))
    video_thread.start()
    threads.append(video_thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()