import grpc
import time

import lss_pb2
import lss_pb2_grpc


channel = grpc.insecure_channel("10.134.108.231:50051")
stub = lss_pb2_grpc.LSSServiceStub(channel)

req = lss_pb2.LSSRequest()

for drone_id in range(3):
    drone = req.drones.add()
    drone.drone_id = drone_id

    for cam_id in range(4):
        img = drone.images.add()
        img.camera_id = cam_id
        img.data = b""  # 先用空数据
        img.width = 0
        img.height = 0
        img.timestamp = time.time()

resp = stub.Infer(req)

for r in resp.results:
    print(f"Drone {r.drone_id}:")
    for n in r.neighbors:
        print(" ", n)
