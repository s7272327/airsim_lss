import airsim
import numpy as np
import cv2
import time
# 连接到 AirSim
client = airsim.VehicleClient()
client.confirmConnection()

# 让摄像头固定在高空俯视
camera_pose = airsim.Pose(airsim.Vector3r(0, 0, -1500), airsim.to_quaternion(-1.57, 0, 0))
client.simSetCameraPose("0", camera_pose)

# 扩大视角，确保能看到更大的区域
client.simSetCameraFov("0", 120)

time.sleep(1)  # 确保相机稳定

# 获取高分辨率地图
responses = client.simGetImages([
    airsim.ImageRequest("0", airsim.ImageType.Segmentation, False, False)
])

# 处理图片
img_data = np.frombuffer(responses[0].image_data_uint8, dtype=np.uint8)
img = img_data.reshape(responses[0].height, responses[0].width, 3)

# 保存地图
cv2.imwrite("global_map.png", img)
print("✅ 高空全景地图已保存：global_map.png")
