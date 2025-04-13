import airsim
import numpy as np
import cv2
import time
# 无人机摄像头编号及含义(camera_name)
# 摄像机0：无人机的前方视角
# 摄像机1：无人机的后方视角
# 摄像机2：无人机的底部视角，可以用于检测地面和障碍物
# 摄像机3：无人机的顶部视角，可以用于拍摄俯视图或进行目标跟踪
# 摄像机4：无人机的左侧视角
# 摄像机5：无人机的右侧视角


# 使用图像API能够获取到的8种图像类型

# Scene：场景视图图片，即俯视图，可以看到整个场景的情况。                                   airsim.ImageType.Scene
# DepthPlanar：平面深度图片，可以获取场景中每个像素点到相机的距离。                          airsim.ImageType.DepthPlanar
# DepthPerspective：透视深度图片，可以获取场景中每个像素点到相机的距离。                     airsim.ImageType.DepthPerspective
# DepthVis：深度可视化图片，可以将深度图像转换为RGB图像，方便观察。                          airsim.ImageType.DepthVis
# DisparityNormalized：视差归一化图片，可以获取场景中每个像素点的视差值，用于计算深度信息。     airsim.ImageType.DisparityNormalized
# Segmentation：分割图片，可以将场景中的不同物体或区域分别标记出来，方便进行目标检测和分割。      airsim.ImageType.Segmentation
# SurfaceNormals：表面法线图片，可以获取场景中每个像素点的法线方向，用于计算光照和阴影效果。      airsim.ImageType.SurfaceNormals
# Infrared：红外线图片，可以获取场景中的红外线图像，用于热成像和红外线探测等应用。               airsim.ImageType.Infrared

# 连接到AirSim模拟器
drone_name = 'Drone1'
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True, vehicle_name=drone_name)
client.armDisarm(True, vehicle_name=drone_name)

# 起飞
# client.takeoffAsync(vehicle_name=drone_name).join()

# 不同的飞行路径（可以根据需要调整）

# client.moveToPositionAsync(0, 0, -5, 3, vehicle_name=drone_name).join()
# time.sleep(2)
# drone_state = client.simGetGroundTruthKinematics(vehicle_name=drone_name)
# position = drone_state.position
# x, y, z = position.x_val, position.y_val, position.z_val
# print(f"无人机位置0：X={x}, Y={y}, Z={z}")
#
# client.moveToPositionAsync(10, 0, -2, 5, vehicle_name=drone_name).join()
# client.hoverAsync(vehicle_name=drone_name).join()

#一次获取一张图片
current_time = time.time()  # 获取当前时间的时间戳
print(f"Current timestamp0: {current_time}")
response = client.simGetImage('1',  airsim.ImageType.Scene, vehicle_name=drone_name)
f = open('scene7.png', 'wb')
f.write(response)
f.close()
current_time = time.time()  # 获取当前时间的时间戳
print(f"Current timestamp1: {current_time}")
# #获取无损无压缩图
# img_raw = client.simGetImages([airsim.ImageRequest(5, airsim.ImageType.Scene, False, False)])[0]
# img1d = np.frombuffer(img_raw.image_data_uint8, dtype=np.uint8)
# img_bgr = img1d.reshape(img_raw.height, img_raw.width, 3)
# cv2.imwrite('scene2.png', img_bgr)

drone_state = client.simGetGroundTruthKinematics(vehicle_name=drone_name)
position = drone_state.position
x, y, z = position.x_val, position.y_val, position.z_val
print(f"无人机位置0：X={x}, Y={y}, Z={z}")

# drone_name = 'Drone2'
# client = airsim.MultirotorClient()
# client.confirmConnection()
# client.enableApiControl(True, vehicle_name=drone_name)
# client.armDisarm(True, vehicle_name=drone_name)
#
# # 起飞
# client.takeoffAsync(vehicle_name=drone_name).join()
#
# # 不同的飞行路径（可以根据需要调整）
#
# client.moveToPositionAsync(0, 0, -6, 3, vehicle_name=drone_name).join()
# client.moveToPositionAsync(0, -2, -6, 1, vehicle_name=drone_name).join()
# time.sleep(2)
# drone_state = client.simGetGroundTruthKinematics(vehicle_name=drone_name)
# position = drone_state.position
# x, y, z = position.x_val, position.y_val, position.z_val
# print(f"无人机位置0：X={x}, Y={y}, Z={z}")

