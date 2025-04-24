import os
import json

def merge_json_files(input_dir, file_prefix, output_filename):
    merged_data = []

    for filename in os.listdir(input_dir):
        if filename.startswith(file_prefix + "_") and filename.endswith(".json"):
            filepath = os.path.join(input_dir, filename)
            print(f"🔍 正在读取: {filepath}")
            with open(filepath, "r") as f:
                try:
                    data = json.load(f)
                    if isinstance(data, list):
                        merged_data.extend(data)
                    else:
                        print(f"⚠️ 跳过（非list）: {filename}")
                except Exception as e:
                    print(f"❌ 读取失败: {filename}，错误：{e}")

    my_base_dir = os.path.join("dataset", "mydataset", "mini", "v1.0-mini")
    output_path = os.path.join(my_base_dir, output_filename)
    with open(output_path, "w") as f:
        json.dump(merged_data, f, indent=4)
    print(f"✅ 合并完成: {output_path}")


if __name__ == "__main__":
    base_dir = "dataset"  # 你所有子目录的上层路径

    # 文件夹名 和 对应输出文件名配置
    folder_config = {
        "sample": "sample.json",
        "sample_data": "sample_data.json",
        "sample_annotation": "sample_annotation.json",
        "ego_pose": "ego_pose.json",
        "instance": "instance.json",
        "scene": "scene.json"
    }

    for folder_name, output_filename in folder_config.items():
        folder_path = os.path.join(base_dir, folder_name)
        merge_json_files(folder_path, folder_name, output_filename)

