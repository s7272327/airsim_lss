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

#定义无人机飞行数据格式
DroneState = namedtuple("DroneState", ["timestamp", "x", "y", "z", "qx", "qy", "qz", "qw"])

#################这里记录数据集中的场景##################
#"downtown_west_1"

scene_name = "downtown_west_1"

#加载数据
with open(f"drones_states_{scene_name}.pkl", "rb") as f:
    drones_states = pickle.load(f)
def create_directory(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def delete_directory(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

def append_to_json_list(file_path, new_data_list):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing = json.load(f)
    else:
        existing = []
    existing.extend(new_data_list)
    with open(file_path, "w") as f:
        json.dump(existing, f, indent=4)


def capture_video(parent_folder,folder_list,client, drone_list):
    # 转置：得到每个时间戳所有无人机的状态（前提是各无人机帧数一致，时间同步）
    states_by_time = list(zip(*drones_states))

    for timestamp_idx, drone_states_at_time in enumerate(states_by_time):
        print(f"第 {timestamp_idx} 个时间点：")
        for drone_idx, state in enumerate(drone_states_at_time):
            position = [state.x, state.y, state.z]
            print(position)
            orientation = [state.qx, state.qy, state.qz, state.qw]
            client.simSetVehiclePose(
                airsim.Pose(airsim.Vector3r(*position), airsim.Quaternionr(*orientation)),
                ignore_collision=True,
                vehicle_name=f"Drone{drone_idx}"
            )
        # 获取压缩的PNG图像
        responses = client.simGetImages([
            airsim.ImageRequest(0, airsim.ImageType.Scene, False, True),
            airsim.ImageRequest(1, airsim.ImageType.Scene, False, True),
            airsim.ImageRequest(2, airsim.ImageType.Scene, False, True),
            airsim.ImageRequest(4, airsim.ImageType.Scene, False, True),
        ], vehicle_name=drone_list[0])

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
                image_filename = os.path.join(folder_path, f"{scene_name}_{timestamp_idx}_{camera_names[i]}.jpg")

                # 将图像保存为JPG文件
                img.save(image_filename, format="JPEG")
def main():

    drone_names = ['Drone0', 'Drone1', 'Drone2', 'Drone3']  # 无人机名称
    folder_list = ['CAM_FRONT', 'CAM_RIGHT', 'CAM_LEFT', 'CAM_BACK']  # 视频存放文件夹
    parent_folder = "mydataset\mini\samples"

    #根据定格的路线采集图片
    capture_video(parent_folder, folder_list, airsim.MultirotorClient(), drone_names)

    cam_id = [0, 1, 2, 4]
    print(f"开始制作数据集标签")
    ###################将数据转换成nusence数据格式#########################

    #output_dir = os.path.join(parent_folder, "v1.0-mini")
    my_scene = scene_name
    #创建scene.json
    scene_list = []
    sample_count = len(drones_states[0])
    time_stamp_first = drones_states[0][0].timestamp
    first_sample_token = f"sample_{my_scene}_{time_stamp_first}"
    time_stamp_last = drones_states[0][-1].timestamp
    last_sample_token = f"sample_{my_scene}_{time_stamp_last}"
    scene_list.append({
        "token": my_scene,
        "log_token": "",
        "nbr_samples": sample_count,
        "first_sample_token": first_sample_token,
        "last_sample_token": last_sample_token,
        "name": f"name_{my_scene}",
        "description": ""
    })
    with open((f"dataset/scene/scene_{my_scene}.json"), "w") as f:
        json.dump(scene_list, f, indent=4)
    # 创建ego_pose和smaple_data以及sample
    ego_pose_list = []
    sample_data_list = []
    sample_list = []
    camera_names = ["front", "right", "left", "back"]
    x0 = 1.5
    y0 = 0
    z0 = -0.08 #setting文件里设置的z为0，这里z为airsim实际返回的坐标，应该是无人机中心距离地面的距离
    for index,state in enumerate(drones_states[0]):  # 遍历自身无人机的所有时间戳数据
        mystate_x = state.x + x0
        mystate_y = state.y + y0
        mystate_z = state.z + z0
        #存储ego_pose
        ego_pose_list.append({
            "token": f"ego_pose_{my_scene}_{state.timestamp}",
            "timestamp": int(state.timestamp * 1e9),  # 转换为纳秒
            "rotation": [state.qw, state.qx, state.qy, state.qz],
            "translation": [mystate_x, mystate_y, mystate_z]
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
            filename = f"samples/{folder_list[i]}/{my_scene}_{index}_{cam_name}.jpg"  # 这里假设你存的文件名是 image_0.jpg, image_1.jpg 依次递增
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
            calibrated_can_token = f"calibrated_sensor_{my_scene}_{cam_name}"
            #生成sample_data(将图像关联到时间戳）
            sample_data_list.append({
                "token": data_token,
                "sample_token": sample_token,
                "ego_pose_token": ego_pose_token,
                "calibrated_sensor_token": calibrated_can_token,
                "timestamp": int(state.timestamp * 1e9),
                "fileformat": "jpg",
                "is_key_frame": "true",
                "height": "900",
                "weight": "1600",
                "filename": filename,
                "prev": pre_token,  # 记录前一帧
                "next": next_token
            })

    with open(f"dataset/sample_data/sample_data_{my_scene}.json", "w") as f:
        json.dump(sample_data_list, f, indent=4)

    with open(f"dataset/ego_pose/ego_pose_{my_scene}.json", "w") as f:
        json.dump(ego_pose_list, f, indent=4)

    with open(f"dataset/sample/sample_{my_scene}.json", "w") as f:
        json.dump(sample_list, f, indent=4)

    #创建sample_annotation和instance.json(主要记录nbr和first,last_anoation)
    sample_annotations = []
    instance = []

    # 为每架无人机创建 instance_token
    num_drones = 3  # 4 架其他无人机
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
        z0 = -0.08
        # 注意这里idx虽然是从0开始，但遍历的是drones_states[1:]，但0对应原来的1号机
        #这里将droneidx恢复为原始编号
        drone_idx_a = drone_idx + 1
        if drone_idx_a == 1:
            x0 = 2
            y0 = -0.25
        elif drone_idx_a == 2:
            x0 = 1.5
            y0 = 0.5
        elif drone_idx_a == 3:
            x0 = 1
            y0 = -0.5
        else:
            x0 = 0
            y0 = 0
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
    with open(f"dataset/sample_annotation/sample_annotation_{my_scene}.json", "w") as f:
        json.dump(sample_annotations, f, indent=4)

    with open(f"dataset/instance/instance_{my_scene}.json", "w") as f:
        json.dump(instance, f, indent=4)

if __name__ == "__main__":
    main()