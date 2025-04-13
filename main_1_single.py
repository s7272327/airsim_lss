
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
def capture_video(parent_folder,folder_list,client, drone_list, duration=20, interval=0.1):
    start_time = time.time()
    count = 0
    for _ in drone_list:
        drone_states = []
        drones_states.append(drone_states)
    while time.time() - start_time < duration:  # 持续拍照直到时间结束
        count = count + 1

        current_time = time.time()  # 获取当前时间的时间戳
        #print(f"时间戳1(获取无人机位置前）: {current_time}")

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

            # print(f"位置编号{count}单独线程{drone}位置：X={curr_x}, Y={curr_y}, Z={curr_z}")
            # print(f"角度（四元数）{orientation}")

        current_time = time.time()  # 获取当前时间的时间戳
        #print(f"时间戳2（获取位置后，图像前）: {current_time}")

        # 获取压缩的PNG图像
        responses = client.simGetImages([
            airsim.ImageRequest(0, airsim.ImageType.Scene, False, True),
            airsim.ImageRequest(1, airsim.ImageType.Scene, False, True),
            airsim.ImageRequest(2, airsim.ImageType.Scene, False, True),
            airsim.ImageRequest(4, airsim.ImageType.Scene, False, True),
        ], vehicle_name=drone_list[0])


        current_time = time.time()  # 获取当前时间的时间戳
        #print(f"时间戳3（获取图像后，存储图像前）: {current_time}")

        camera_names = ["front", "right", "left", "back"]
        for i, response in enumerate(responses):
                #将图像数据转换为PIL Image对象
                img_data = response.image_data_uint8
                img = Image.open(io.BytesIO(img_data))

                # 如果图像是RGBA模式，转换为RGB模式
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                # 生成文件名
                folder_path = os.path.join(parent_folder, folder_list[i])
                image_filename = os.path.join(folder_path, f"{count}_{camera_names[i]}.jpg")

                # 将图像保存为JPG文件
                img.save(image_filename, format="JPEG")

        current_time = time.time()  # 获取当前时间的时间戳
        #print(f"时间戳4（存储图像后）: {current_time}")


        # time.sleep(interval)  # 控制拍照间隔


# 无人机飞行路径的函数
def fly_drone(client, drone_name, duration):

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
        client.moveToPositionAsync(1.5, 0, -3, 0.75, vehicle_name=drone_name).join()
    elif drone_name == 'Drone1': #右侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, 1.5, -3, 0.75, vehicle_name=drone_name).join()
    elif drone_name == 'Drone2':#左侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(0, -1.5, -3, 0.75, vehicle_name=drone_name).join()
    elif drone_name == 'Drone4':#后侧相机
        client.moveToPositionAsync(0, 0, -3, 1.5, vehicle_name=drone_name).join()
        client.moveToPositionAsync(-4, 0, -3, 0.75, vehicle_name=drone_name).join()
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

    #删除执之前的文件夹，创建新的文件夹
    drone_names = ['Drone', 'Drone0', 'Drone1', 'Drone2', 'Drone4']  # 无人机名称
    folder_list = ['CAM_FRONT', 'CAM_RIGHT', 'CAM_LEFT', 'CAM_BACK']  # 视频存放文件夹
    parent_folder = "mydataset\mini\samples"
    for folder_name in folder_list:
        folder_path = os.path.join(parent_folder, folder_name)
        #删除先前记录的
        delete_directory(folder_path)
        #创建新文件夹
        create_directory(folder_path)

    #创建线程
    cam_id = [0, 1, 2, 4]
    duration = 30  # 视频捕获时长
    threads = []
    #创建飞行线程
    # 为每架无人机创建一个线程
    for i in range(len(drone_names)):
        thread = threading.Thread(target=fly_drone,
                                  args=(airsim.MultirotorClient(), drone_names[i], duration))
        threads.append(thread)
        thread.start()
    #创建拍摄线程
    video_thread = threading.Thread(target=capture_video, args=(parent_folder,folder_list,airsim.MultirotorClient(), drone_names))
    threads.append(video_thread)
    video_thread.start()
    # 等待所有线程完成
    for thread in threads:
        thread.join()

    print(f"开始制作数据集标签")
    ###################将数据转换成nusence数据格式#########################
    #创建ego_pose和smaple_data以及sample
    #更新parent folder
    parent_folder = "mydataset\mini"
    output_dir = os.path.join(parent_folder, "v1.0-mini")
    my_scene = "downtown_west"

    ego_pose_list = []
    sample_data_list = []
    sample_list = []
    camera_names = ["front", "right", "left", "back"]
    for index,state in enumerate(drones_states[0]):  # 遍历自身无人机的所有时间戳数据
        #存储ego_pose
        ego_pose_list.append({
            "token": f"ego_pose_{my_scene}_{state.timestamp}",
            "timestamp": int(state.timestamp * 1e9),  # 转换为纳秒
            "rotation": [state.qw, state.qx, state.qy, state.qz],
            "translation": [state.x, state.y, state.z]
        })
        #存储sample
        if index == 0:
            sample_pre_token = ""
        else:
            time_stamp_pre = drones_states[0][index - 1].timestamp
            sample_pre_token = f"sample_{my_scene}_{time_stamp_pre}"
        if index == len(drones_states[0]) - 1:
            sample_next_token = ""
        else:
            time_stamp_next = drones_states[0][index + 1].timestamp
            sample_next_token = f"sample_{my_scene}_{time_stamp_next}"
        sample_list.append({
            "token": f"sample_{my_scene}_{state.timestamp}",
            "timestamp": int(state.timestamp * 1e9),  # 转换为纳秒
            "prev": sample_pre_token,
            "next": sample_next_token,
            "scene_token": my_scene
        })

        for i, cam_name in enumerate(camera_names):

            data_token = f"sample_data_{my_scene}_{state.timestamp}_{cam_name}"
            filename = f"samples/{folder_list[i]}/{index + 1}_{cam_name}.jpg"  # 这里假设你存的文件名是 image_0.jpg, image_1.jpg 依次递增
            sample_token = f"sample_{my_scene}_{state.timestamp}"
            ego_pose_token = f"ego_pose_{my_scene}_{state.timestamp}"
            if index == 0:
                pre_token = ""
            else:
                time_stamp_pre = drones_states[0][index - 1].timestamp
                pre_token = f"sample_data_{my_scene}_{time_stamp_pre}_{cam_name}"
            if index == len(drones_states[0]) - 1:
                next_token = ""
            else:
                time_stamp_next = drones_states[0][index + 1].timestamp
                next_token = f"sample_data_{my_scene}_{time_stamp_next}_{cam_name}"
            calibrated_can_token = f"calibrated_sensor_downtown_west_{cam_name}"
            #生成sample_data(将图像关联到时间戳）
            sample_data_list.append({
                "token": data_token,
                "sample_token": sample_token,
                "ego_pose_token": ego_pose_token,
                "calibrated_sensor_token": calibrated_can_token,
                "timestamp": int(state.timestamp * 1e9),
                "fileformat": "jpg",
                "is_key_frame": "true",
                "height": "480",
                "weight": "640",
                "filename": filename,
                "prev": pre_token,  # 记录前一帧
                "next": next_token
            })

    # 保存为 JSON 文件
    with open(os.path.join(output_dir, "sample_data.json"), "w") as f:
        json.dump(sample_data_list, f, indent=4)

    with open(os.path.join(output_dir, "ego_pose.json"), "w") as f:
        json.dump(ego_pose_list, f, indent=4)

    with open(os.path.join(output_dir, "sample.json"), "w") as f:
        json.dump(sample_list, f, indent=4)


    #创建sample_annotation和instance.json(主要记录nbr和first,last_anoation)
    sample_annotations = []
    instance = []

    # 为每架无人机创建 instance_token
    num_drones = 4  # 4 架其他无人机
    instance_tokens = [str(uuid.uuid4()) for _ in range(num_drones)]
    for drone_idx, drone_states in enumerate(drones_states[1:]):
        prev_token = ""  # 初始化 prev_token
        pre_next_token = str(uuid.uuid4())
        #为instance初始化first_annotation_token和last_annotation_token
        first_annotation_token = ""
        last_annotation_token = ""
        #airsim返回的位置坐标都以自身启动点为0点，这里加上相对真实零点的偏移
        x0 = 0
        y0 = 0
        if drone_idx == 0:
            x0 = 0.5
        elif drone_idx == 1:
            y0 = 0.5
        elif drone_idx == 2:
            y0 = -0.5
        else:
            x0 = -0.5
        # 遍历该无人机的所有时间戳
        for timestamp_idx, state in enumerate(drone_states):
            #生成pre_token
            if prev_token == "":
                annotation_token = str(uuid.uuid4())  # 生成当前的 annotation_token
                first_annotation_token = annotation_token
            else:
                annotation_token = pre_next_token
            # 如果不是最后一个时间戳，就预生成 next_token
            if timestamp_idx < len(drone_states) - 1:
                next_token = str(uuid.uuid4())
                pre_next_token = next_token
            else:
                last_annotation_token = annotation_token
                next_token = ""
            # 生成 sample_token（样本关联）
            sample_token = f"sample_{my_scene}_{state.timestamp}"
            #修正state的x,y
            mystate_x = state.x + x0
            mystate_y = state.y + y0

            # 创建 sample_annotation
            sample_annotations.append({
                "token": annotation_token,
                "sample_token": sample_token,
                "instance_token": instance_tokens[drone_idx],
                "visibility_token": "4",
                "attribute_tokens": [],
                "translation": [mystate_x, mystate_y, state.z],
                "size": [0.23, 0.23, 0.16],  # 设定合适尺寸
                "rotation": [state.qw, state.qx, state.qy, state.qz],
                "prev": prev_token,
                "next": next_token,
                "num_lidar_pts": 0,
                "num_radar_pts": 0
            })
            prev_token = annotation_token  # 更新 prev_token
        print(drone_idx)
        # 创建 instance.json
        instance.append({
            "token": instance_tokens[drone_idx],
            "category_token": "dji_mavic",
            "nbr_annotations": len(drone_states) + 1,
            "first_annotation_token": first_annotation_token,
            "last_annotation_token": last_annotation_token
        }
        )
    # 存储数据
    with open(os.path.join(output_dir, "sample_annotation.json"), "w") as f:
        json.dump(sample_annotations, f, indent=4)

    with open(os.path.join(output_dir, "instance.json"), "w") as f:
        json.dump(instance, f, indent=4)

if __name__ == "__main__":
    main()