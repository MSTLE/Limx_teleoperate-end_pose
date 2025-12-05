#!/usr/bin/env python3
"""
Step 7: Quest VR实时控制机器人 - Pinch控制 + 平滑运动版本

主要功能：
1. 手部追踪：使用 pinch（捏合）控制夹爪
2. 平滑滤波：指数平滑，让动作更丝滑
3. 速度限制：可选的速度限制功能
4. 头部控制：VR头显俯仰角实时控制机器人头部姿态
5. baselink坐标系：位置控制基于机器人腰部baselink坐标系

控制映射：
- 双臂位置/姿态：跟随VR手部或手柄位置（baselink坐标系）
- 头部姿态：跟随VR头显俯仰角（范围：-30° ~ 45°）
- 夹爪：Pinch手势或手柄Grip按钮

坐标系说明：
- 参考坐标系：base_link（机器人腰部）
- X轴（红色）：机器人前进方向
- Y轴（绿色）：正方向向左
- Z轴（蓝色）：竖直向上

夹爪控制：
- Pinch值范围: 0.0(食指拇指捏紧) ~ 0.1+(分开)
- 夹爪映射: 
  * pinch <= 0.0 → 夹爪完全闭合 (0)
  * pinch >= 0.1 → 夹爪完全张开 (1000)
  * 中间值线性插值

平滑控制参数（RobotController类）：
- enable_smoothing: 是否启用平滑 (默认True)
- smoothing_factor: 平滑系数 0.0-1.0 (默认0.3，推荐0.2-0.5)
  * 越小 = 响应越快，越抖
  * 越大 = 越平滑，延迟越大
- enable_velocity_limit: 是否限速 (默认False)
- max_velocity: 最大速度 m/s (默认0.15)
- motion_scale: 运动缩放系数 (默认1.5，推荐1.5-2.0)
  * 放大VR手部移动映射到机器人末端的幅度
  * 越大 = 机器人移动范围越大

可调参数位置：
- PINCH_MAX: 第577行附近，默认0.10
- smoothing_factor: 第86行，默认0.3
- max_velocity: 第83行，默认0.15
- motion_scale: 第71行，默认1.5（或在启动时交互式设置）
"""

import numpy as np
import json
import time
import threading
import websocket
import uuid
from multiprocessing import shared_memory
from televuer.tv_wrapper import TeleVuerWrapper
import os
from pathlib import Path
import pickle
import sys

# 导入图像客户端
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
from image_service.image_client import ImageClient


class RobotController:
    """机器人控制器"""
    def __init__(self, robot_ip="10.192.1.2", enable_smoothing=True, enable_velocity_limit=False, motion_scale=1.5):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        self.ee_pose_response = None  # 用于接收位姿查询响应
        
        # 基础位姿（baselink坐标系下的初始绝对位置，标定时设置）
        self.base_left_pos = [0.0, 0.0, 0.0]
        self.base_left_quat = [0.0, 0.0, 0.0, 1.0]
        self.base_right_pos = [0.0, 0.0, 0.0]
        self.base_right_quat = [0.0, 0.0, 0.0, 1.0]
        
        # 运动缩放系数（放大VR手部移动）
        self.motion_scale = motion_scale  # 默认1.5倍，可调整为1.0-3.0
        
        # 工作空间限制（baselink坐标系下的绝对范围）
        # 根据机器人实际情况调整这些值
        # x: 前后（红色轴，正方向向前）
        # y: 左右（绿色轴，正方向向左）
        # z: 上下（蓝色轴，正方向向上）
        self.workspace = {
            'x_min': -0.50, 'x_max': 0.80,   # 前后范围
            'y_min': -0.80, 'y_max': 0.80,   # 左右范围
            'z_min': 0.20, 'z_max': 1.50     # 高度范围（腰部以上）
        }
        
        # 运动控制参数
        self.enable_smoothing = enable_smoothing
        self.enable_velocity_limit = enable_velocity_limit
        self.max_velocity = 0.15  # m/s (仅在enable_velocity_limit=True时生效)
        
        # 平滑滤波参数 (0.0=无平滑, 1.0=完全平滑/不动)
        self.smoothing_factor = 0.3  # 推荐范围: 0.2-0.5
        
        # 平滑状态变量
        self.smoothed_left_pos = None
        self.smoothed_right_pos = None
        self.smoothed_left_gripper = None
        self.smoothed_right_gripper = None
        self.last_time = None
        
        # 夹爪参数
        self.gripper_speed = 500
        self.gripper_force = 300
        
    def on_message(self, ws, message):
        data = json.loads(message)
        if 'accid' in data and not self.accid:
            self.accid = data['accid']
            print(f"✅ 已连接: {self.accid}")
        
        # 处理位姿查询响应
        if data.get('title') == 'response_get_ub_manip_ee_pose':
            self.ee_pose_response = data.get('data', {})
        
    def on_open(self, ws):
        self.connected = True
        
    def on_error(self, ws, error):
        print(f"❌ WebSocket错误: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        self.connected = False
        print("🔌 WebSocket断开")
        
    def connect(self):
        """连接机器人"""
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_open=self.on_open,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        wst = threading.Thread(target=self.ws.run_forever, daemon=True)
        wst.start()
        
        timeout = 5
        start = time.time()
        while not self.connected and (time.time() - start) < timeout:
            time.sleep(0.1)
        
        if not self.connected:
            raise Exception("连接超时")
        
        time.sleep(1)
        return True
        
    def send_command(self, title, data=None):
        """发送命令"""
        msg = {
            "accid": self.accid,
            "title": title,
            "timestamp": int(time.time() * 1000),
            "guid": str(uuid.uuid4()).replace('-', ''),
            "data": data or {}
        }
        self.ws.send(json.dumps(msg))
    
    def get_current_ee_pose(self):
        """获取当前末端执行器位姿（baselink坐标系）"""
        # 重置响应标志
        self.ee_pose_response = None
        
        # 发送请求
        self.send_command("request_get_ub_manip_ee_pose", {})
        
        # 等待响应（最多2秒）
        timeout = 2.0
        start = time.time()
        while self.ee_pose_response is None and (time.time() - start) < timeout:
            time.sleep(0.01)
        
        if self.ee_pose_response and self.ee_pose_response.get('result') == 'success':
            return {
                'left_hand_pos': self.ee_pose_response.get('left_hand_pos'),
                'left_hand_quat': self.ee_pose_response.get('left_hand_quat'),
                'right_hand_pos': self.ee_pose_response.get('right_hand_pos'),
                'right_hand_quat': self.ee_pose_response.get('right_hand_quat')
            }
        else:
            print("⚠️  获取机器人位姿失败")
            return None
        
    def enter_damping(self):
        """进入阻尼模式"""
        self.send_command("request_damping")
        time.sleep(2)
        
    def enter_prepare(self):
        """进入准备模式"""
        self.send_command("request_prepare")
        time.sleep(3)
        
    def set_ub_manip_mode(self, mode):
        """设置上肢操作模式"""
        self.send_command("request_set_ub_manip_mode", {"mode": mode})
        time.sleep(3 if mode in [0, 2] else 1)
        
    def set_pose(self, left_pos, left_quat, right_pos, right_quat, head_quat=None):
        """设置机器人位姿"""
        data = {
            "head_quat": head_quat or [0.0, 0.0, 0.0, 1.0],
            "left_hand_pos": left_pos,
            "left_hand_quat": left_quat,
            "right_hand_pos": right_pos,
            "right_hand_quat": right_quat
        }
        self.send_command("request_set_ub_manip_ee_pose", data)
        
    def clip_to_workspace(self, pos):
        """限制位置到安全工作空间（baselink坐标系下的绝对位置）"""
        return [
            np.clip(pos[0], self.workspace['x_min'], self.workspace['x_max']),
            np.clip(pos[1], self.workspace['y_min'], self.workspace['y_max']),
            np.clip(pos[2], self.workspace['z_min'], self.workspace['z_max'])
        ]
    
    def smooth_position(self, target_pos, smoothed_pos):
        """指数平滑滤波 - 位置"""
        if not self.enable_smoothing or smoothed_pos is None:
            return list(target_pos)  # 确保返回列表而不是numpy数组
        
        # 指数平滑: output = alpha * new + (1-alpha) * old
        alpha = 1.0 - self.smoothing_factor
        smoothed = alpha * np.array(target_pos) + self.smoothing_factor * np.array(smoothed_pos)
        return smoothed.tolist()  # 转换为列表
    
    def smooth_gripper(self, target_gripper, smoothed_gripper):
        """指数平滑滤波 - 夹爪"""
        if not self.enable_smoothing or smoothed_gripper is None:
            return target_gripper
        
        alpha = 1.0 - self.smoothing_factor * 0.7  # 夹爪响应稍快一些
        return alpha * target_gripper + self.smoothing_factor * 0.7 * smoothed_gripper
    
    def limit_velocity(self, target_pos, current_pos, dt):
        """限制速度"""
        if not self.enable_velocity_limit or current_pos is None or dt <= 0:
            return list(target_pos)  # 确保返回列表
        
        target = np.array(target_pos)
        current = np.array(current_pos)
        delta = target - current
        distance = np.linalg.norm(delta)
        
        max_distance = self.max_velocity * dt
        if distance > max_distance:
            # 限制移动距离
            delta = delta / distance * max_distance
            return (current + delta).tolist()
        
        return list(target_pos)  # 确保返回列表
    
    def set_gripper(self, left_opening=None, right_opening=None, apply_smoothing=True):
        """控制夹爪开口度（带平滑）"""
        # 应用平滑
        if apply_smoothing:
            if left_opening is not None:
                left_opening = self.smooth_gripper(left_opening, self.smoothed_left_gripper)
                self.smoothed_left_gripper = left_opening
            
            if right_opening is not None:
                right_opening = self.smooth_gripper(right_opening, self.smoothed_right_gripper)
                self.smoothed_right_gripper = right_opening
        
        data = {}
        
        if left_opening is not None:
            left_opening = int(np.clip(left_opening, 0, 1000))
            data["left_opening"] = left_opening
            data["left_speed"] = self.gripper_speed
            data["left_force"] = self.gripper_force
            data["left_mode"] = 3
        
        if right_opening is not None:
            right_opening = int(np.clip(right_opening, 0, 1000))
            data["right_opening"] = right_opening
            data["right_speed"] = self.gripper_speed
            data["right_force"] = self.gripper_force
            data["right_mode"] = 3
        
        if data:
            self.send_command("request_set_claw_cmd", data)
    
    def set_pose_smooth(self, left_pos, left_quat, right_pos, right_quat, head_quat=None, dt=0.033):
        """设置机器人位姿（带平滑和速度限制）"""
        # 应用速度限制
        if self.enable_velocity_limit:
            left_pos = self.limit_velocity(left_pos, self.smoothed_left_pos, dt)
            right_pos = self.limit_velocity(right_pos, self.smoothed_right_pos, dt)
        
        # 应用平滑
        if self.enable_smoothing:
            left_pos = self.smooth_position(left_pos, self.smoothed_left_pos)
            right_pos = self.smooth_position(right_pos, self.smoothed_right_pos)
            
            # 更新平滑状态
            self.smoothed_left_pos = left_pos
            self.smoothed_right_pos = right_pos
        
        # 发送指令
        self.set_pose(left_pos, left_quat, right_pos, right_quat, head_quat)


def matrix_to_pos_quat(matrix):
    """从4x4矩阵提取位置和四元数"""
    pos = matrix[:3, 3].tolist()
    
    R = matrix[:3, :3]
    trace = np.trace(R)
    
    if trace > 0:
        s = 0.5 / np.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (R[2, 1] - R[1, 2]) * s
        y = (R[0, 2] - R[2, 0]) * s
        z = (R[1, 0] - R[0, 1]) * s
    else:
        if R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2])
            w = (R[2, 1] - R[1, 2]) / s
            x = 0.25 * s
            y = (R[0, 1] + R[1, 0]) / s
            z = (R[0, 2] + R[2, 0]) / s
        elif R[1, 1] > R[2, 2]:
            s = 2.0 * np.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2])
            w = (R[0, 2] - R[2, 0]) / s
            x = (R[0, 1] + R[1, 0]) / s
            y = 0.25 * s
            z = (R[1, 2] + R[2, 1]) / s
        else:
            s = 2.0 * np.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1])
            w = (R[1, 0] - R[0, 1]) / s
            x = (R[0, 2] + R[2, 0]) / s
            y = (R[1, 2] + R[2, 1]) / s
            z = 0.25 * s
    
    quat = [x, y, z, w]
    return pos, quat


def save_calibration(calib_left, calib_right, robot_base_left_pos, robot_base_right_pos, filename="vr_calibration.pkl"):
    """保存标定数据"""
    calib_data = {
        'calib_left': calib_left,  # VR左手参考位置
        'calib_right': calib_right,  # VR右手参考位置
        'robot_base_left_pos': robot_base_left_pos,  # 机器人左手初始绝对位置（baselink坐标系）
        'robot_base_right_pos': robot_base_right_pos,  # 机器人右手初始绝对位置（baselink坐标系）
        'timestamp': time.time()
    }
    with open(filename, 'wb') as f:
        pickle.dump(calib_data, f)
    print(f"✅ 标定数据已保存到 {filename}")


def load_calibration(filename="vr_calibration.pkl"):
    """加载标定数据"""
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'rb') as f:
            calib_data = pickle.load(f)
        
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(calib_data['timestamp']))
        print(f"\n📂 找到标定文件:")
        print(f"   保存时间: {timestamp}")
        print(f"   VR左手参考: {calib_data['calib_left'][:3, 3]}")
        print(f"   VR右手参考: {calib_data['calib_right'][:3, 3]}")
        
        robot_base_left_pos = calib_data.get('robot_base_left_pos', None)
        robot_base_right_pos = calib_data.get('robot_base_right_pos', None)
        
        if robot_base_left_pos:
            print(f"   机器人左手初始位置: {robot_base_left_pos}")
            print(f"   机器人右手初始位置: {robot_base_right_pos}")
        
        return calib_data['calib_left'], calib_data['calib_right'], robot_base_left_pos, robot_base_right_pos
    except Exception as e:
        print(f"❌ 加载标定失败: {e}")
        return None


def calibrate_vr(tv_wrapper):
    """执行VR标定"""
    print("📊 开始采集标定数据（保持双手不动）...")
    
    calibration_samples = []
    print("   标定中", end='', flush=True)
    for i in range(30):
        tele_data = tv_wrapper.get_motion_state_data()
        calibration_samples.append({
            'left': tele_data.left_arm_pose.copy(),
            'right': tele_data.right_arm_pose.copy()
        })
        time.sleep(1/30)
        if (i+1) % 10 == 0:
            print(".", end='', flush=True)
    
    calib_left = np.mean([s['left'] for s in calibration_samples], axis=0)
    calib_right = np.mean([s['right'] for s in calibration_samples], axis=0)
    
    print(" 完成!")
    print(f"\n✅ 标定成功!")
    print(f"   左手参考位置: {calib_left[:3, 3]}")
    print(f"   右手参考位置: {calib_right[:3, 3]}")
    
    return calib_left, calib_right


def main():
    print("="*60)
    print("Step 7: Meta Quest VR实时控制 (Pinch版本)")
    print("="*60)
    print("\n⚠️  安全检查:")
    print("□ 机器人已悬挂，脚离地≥15cm")
    print("□ SSL证书已生成 (cert.pem, key.pem)")
    print("□ Quest已连接到同一WiFi")
    print("□ 遥控器在手边")
    input("\n✅ 确认后按Enter...")
    
    # 检查SSL证书
    cert_file = Path("cert.pem")
    key_file = Path("key.pem")
    if not cert_file.exists() or not key_file.exists():
        print("\n⚠️  未找到SSL证书！")
        print("运行: python generate_ssl_cert.py")
        return
    
    print("\n初始化VR接口...")
    # 创建虚拟图像共享内存
    img_shape = (480, 640, 3)
    img_shm = shared_memory.SharedMemory(create=True, size=np.prod(img_shape) * np.uint8().itemsize)
    img_array = np.ndarray(img_shape, dtype=np.uint8, buffer=img_shm.buf)
    img_array[:] = 128  # 灰色背景
    
    # 视频回传选项
    print("\n📹 机器人视频回传:")
    print("1. 启用视频回传 - 在Quest中看到机器人摄像头画面")
    print("2. 禁用视频回传 - 仅控制，不显示画面")
    video_choice = input("请选择 [1/2，默认1]: ").strip() or "1"
    enable_video = (video_choice == "1")
    
    robot_ip = "10.192.1.3"  # 机器人IP (从test文件看是10.192.1.3)
    zmq_port = 5556  # ZMQ端口 (使用5556)
    image_client = None
    
    if enable_video:
        print(f"   将从 {robot_ip}:{zmq_port} 接收视频流")
        print(f"   图像形状: {img_shape}")
    
    # 选择模式
    print("\n选择输入模式:")
    print("1. 手柄控制器 (controller)")
    print("2. 手部追踪 (hand tracking) - 使用PINCH控制夹爪")
    mode = input("请选择 [1/2]: ").strip()
    use_hand_tracking = (mode == "2")
    
    # 初始化TeleVuer
    tv_wrapper = TeleVuerWrapper(
        binocular=False,
        use_hand_tracking=use_hand_tracking,
        img_shape=img_shape,
        img_shm_name=img_shm.name,
        return_state_data=True,
        return_hand_rot_data=False,
        cert_file=str(cert_file.absolute()),
        key_file=str(key_file.absolute())
    )
    
    print(f"✅ VR服务已启动")
    print(f"   模式: {'手部追踪(PINCH)' if use_hand_tracking else '手柄控制器'}")
    print(f"\n📱 在Quest中打开浏览器，访问:")
    print(f"   https://vuer.ai?grid=False")
    input("\n等待Quest连接后按Enter开始初始化机器人...")
    
    # 启动视频接收（如果启用）
    if enable_video:
        print(f"\n🚀 启动图像客户端...")
        print(f"   目标服务器: {robot_ip}:{zmq_port}")
        print(f"   共享内存: {img_shm.name}")
        print(f"   图像形状: {img_shape}")
        
        image_client = ImageClient(
            img_shape=img_shape,
            img_shm_name=img_shm.name,
            image_show=False,  # 不显示调试窗口（在VR中显示）
            server_address=robot_ip,
            port=zmq_port,
            enable_stats=False  # 关闭统计信息打印
        )
        image_client.start()
        print(f"✅ 图像客户端已启动")
        print(f"💡 提示: 图像会自动显示在Quest的Vuer界面中")
        print(f"   如果没有画面，请确保机器人端ZMQ服务器正在运行:")
        print(f"   ssh robot@{robot_ip}")
        print(f"   python ros2_to_zmq_bridge.py --camera camera0 --port {zmq_port} --stats")
        time.sleep(2)  # 等待连接建立
    
    # 平滑控制选项（默认启用）
    print("\n🎛️  运动控制选项:")
    print("1. 启用平滑滤波 + 速度限制 (推荐) - 动作丝滑稳定")
    print("2. 仅启用平滑滤波 - 丝滑但不限速")
    print("3. 原始模式 - 无平滑无限速")
    control_choice = input("请选择 [1/2/3，默认1]: ").strip() or "1"
    
    if control_choice == "1":
        enable_smoothing = True
        enable_velocity_limit = True
    elif control_choice == "2":
        enable_smoothing = True
        enable_velocity_limit = False
    else:
        enable_smoothing = False
        enable_velocity_limit = False
    
    # 运动缩放系数设置
    print("\n🔧 运动缩放系数 (放大VR手部移动):")
    print("   推荐值: 1.5-2.0 (默认1.5)")
    print("   说明: 系数越大，机器人手臂移动幅度越大")
    motion_scale_input = input("请输入缩放系数 [默认1.5]: ").strip()
    try:
        motion_scale = float(motion_scale_input) if motion_scale_input else 1.5
        motion_scale = max(0.5, min(motion_scale, 3.0))  # 限制在0.5-3.0范围
    except ValueError:
        motion_scale = 1.5
        print("   ⚠️  输入无效，使用默认值1.5")
    
    # 连接机器人
    print("\n连接机器人...")
    robot = RobotController(
        enable_smoothing=enable_smoothing,
        enable_velocity_limit=enable_velocity_limit,
        motion_scale=motion_scale
    )
    robot.connect()
    
    if enable_smoothing:
        print(f"✅ 平滑滤波已启用 (系数: {robot.smoothing_factor})")
    if enable_velocity_limit:
        print(f"✅ 速度限制已启用 (最大: {robot.max_velocity}m/s)")
    print(f"✅ 运动缩放已设置 (系数: {robot.motion_scale}x)")
    
    # 初始化机器人
    print("\n初始化机器人模式...")
    robot.enter_damping()
    print("✅ 阻尼模式")
    time.sleep(1)
    
    robot.enter_prepare()
    print("✅ 准备模式")
    time.sleep(1)
    
    robot.set_ub_manip_mode(0)
    print("✅ Mode 0 (初始姿态)")
    time.sleep(2)
    
    robot.set_ub_manip_mode(1)
    print("✅ Mode 1 (等待控制)")
    time.sleep(1)
    
    # 标定
    print("\n"+"="*60)
    print("🎯 标定阶段")
    print("="*60)
    
    print("\n⏱️  准备标定，倒计时...")
    print("   请将双手移动到舒适的起始位置")
    for i in range(5, 0, -1):
        print(f"   {i}...", flush=True)
        time.sleep(1)
    print("   ✅ 时间到!\n")
    
    # 标定VR位置
    calib_left, calib_right = calibrate_vr(tv_wrapper)
    
    # 获取机器人当前位置（baselink坐标系）
    print("\n🤖 获取机器人当前位置...")
    robot_pose = robot.get_current_ee_pose()
    
    if robot_pose is None:
        print("❌ 无法获取机器人位置，退出")
        return
    
    robot_base_left_pos = robot_pose['left_hand_pos']
    robot_base_right_pos = robot_pose['right_hand_pos']
    
    # 验证数据有效性
    if robot_base_left_pos is None or robot_base_right_pos is None:
        print("❌ 机器人位置数据无效，退出")
        return
    
    print(f"✅ 机器人左手初始位置（baselink）: {robot_base_left_pos}")
    print(f"✅ 机器人右手初始位置（baselink）: {robot_base_right_pos}")
    
    # 保存标定数据
    save_calibration(calib_left, calib_right, robot_base_left_pos, robot_base_right_pos)
    
    # 将初始位置保存到robot对象
    robot.base_left_pos = robot_base_left_pos
    robot.base_right_pos = robot_base_right_pos
    
    # 主控制循环
    print("\n"+"="*60)
    print("🤖 开始控制! (Ctrl+C退出)")
    print("="*60)
    print("🎯 控制映射:")
    print("   • 双臂：跟随VR手部/手柄位置和姿态")
    print("   • 头部：跟随VR头显俯仰角（-30° ~ 45°）")
    if use_hand_tracking:
        print("   • 夹爪：食指和拇指捏合(pinch)控制开合")
    else:
        print("   • 夹爪：握把(Grip)按钮控制开合")
    print()
    
    try:
        control_rate = 30  # Hz
        dt = 1.0 / control_rate
        
        while True:
            loop_start = time.time()
            
            # 获取VR数据
            tele_data = tv_wrapper.get_motion_state_data()
            
            # 计算VR相对偏移
            left_vr_offset = (tele_data.left_arm_pose[:3, 3] - calib_left[:3, 3]).tolist()
            right_vr_offset = (tele_data.right_arm_pose[:3, 3] - calib_right[:3, 3]).tolist()
            
            # 应用运动缩放系数
            left_vr_offset_scaled = [x * robot.motion_scale for x in left_vr_offset]
            right_vr_offset_scaled = [x * robot.motion_scale for x in right_vr_offset]
            
            # 计算baselink坐标系下的绝对位置 = 初始位置 + 缩放后的VR偏移
            left_target_pos = [
                robot.base_left_pos[0] + left_vr_offset_scaled[0],
                robot.base_left_pos[1] + left_vr_offset_scaled[1],
                robot.base_left_pos[2] + left_vr_offset_scaled[2]
            ]
            right_target_pos = [
                robot.base_right_pos[0] + right_vr_offset_scaled[0],
                robot.base_right_pos[1] + right_vr_offset_scaled[1],
                robot.base_right_pos[2] + right_vr_offset_scaled[2]
            ]
            
            # 限制到安全工作空间
            left_pos_safe = robot.clip_to_workspace(left_target_pos)
            right_pos_safe = robot.clip_to_workspace(right_target_pos)
            
            # 提取四元数（双臂和头部）
            _, left_quat = matrix_to_pos_quat(tele_data.left_arm_pose)
            _, right_quat = matrix_to_pos_quat(tele_data.right_arm_pose)
            _, head_quat = matrix_to_pos_quat(tele_data.head_pose)
            
            # 发送到机器人（带平滑和速度限制）
            robot.set_pose_smooth(
                left_pos=left_pos_safe,
                left_quat=left_quat,
                right_pos=right_pos_safe,
                right_quat=right_quat,
                head_quat=head_quat,
                dt=dt
            )
            
            # 夹爪控制
            if use_hand_tracking:
                # *** 使用PINCH而不是SQUEEZE ***
                # 根据实际测试，有效pinch范围: 0.0(捏紧) ~ 0.1(分开)
                # 映射: pinch=0.0 -> 夹爪=0(闭合), pinch=0.1 -> 夹爪=1000(张开)
                if tele_data.left_pinch_value is not None and tele_data.right_pinch_value is not None:
                    # 定义pinch的有效控制范围
                    PINCH_MAX = 0.10  # 分开到这个值时，夹爪完全张开
                    PINCH_MIN = 0.00  # 捏紧到这个值时，夹爪完全闭合
                    
                    # pinch_value从TeleVuer来的是百分比，需要转换为0-1
                    left_pinch = tele_data.left_pinch_value / 100.0
                    right_pinch = tele_data.right_pinch_value / 100.0
                    
                    # 归一化到0-1，超出范围会被clip
                    # pinch=0.0 -> norm=0.0 -> gripper=0 (闭合)
                    # pinch=0.1 -> norm=1.0 -> gripper=1000 (张开)
                    left_pinch_norm = np.clip(left_pinch / PINCH_MAX, 0.0, 1.0)
                    right_pinch_norm = np.clip(right_pinch / PINCH_MAX, 0.0, 1.0)
                    
                    # 映射到夹爪开口度 [0, 1000]
                    left_gripper = int(left_pinch_norm * 1000)
                    right_gripper = int(right_pinch_norm * 1000)
                    
                    robot.set_gripper(left_opening=left_gripper, right_opening=right_gripper)
            else:
                # 手柄模式：使用握把按钮
                if tele_data.tele_state:
                    left_squeeze = tele_data.tele_state.left_squeeze_ctrl_value
                    right_squeeze = tele_data.tele_state.right_squeeze_ctrl_value
                    left_gripper = int((1.0 - left_squeeze) * 1000)
                    right_gripper = int((1.0 - right_squeeze) * 1000)
                    robot.set_gripper(left_opening=left_gripper, right_opening=right_gripper)
            
            # 打印状态
            if int(time.time() * 3) % 3 == 0:
                gripper_info = ""
                if use_hand_tracking:
                    if tele_data.left_pinch_value is not None:
                        PINCH_MAX = 0.10  # 与控制逻辑保持一致
                        left_p_raw = tele_data.left_pinch_value / 100.0
                        right_p_raw = tele_data.right_pinch_value / 100.0
                        left_p_norm = np.clip(left_p_raw / PINCH_MAX, 0.0, 1.0)
                        right_p_norm = np.clip(right_p_raw / PINCH_MAX, 0.0, 1.0)
                        left_g = int(left_p_norm * 1000)
                        right_g = int(right_p_norm * 1000)
                        gripper_info = f"  夹爪 L:{left_g:4d} R:{right_g:4d} [Pinch: L:{left_p_raw:.3f} R:{right_p_raw:.3f}]"
                elif tele_data.tele_state:
                    left_sq = tele_data.tele_state.left_squeeze_ctrl_value
                    right_sq = tele_data.tele_state.right_squeeze_ctrl_value
                    left_g = int((1.0 - left_sq) * 1000)
                    right_g = int((1.0 - right_sq) * 1000)
                    gripper_info = f"  夹爪 L:{left_g:4d} R:{right_g:4d} [Grip: L:{left_sq:.2f} R:{right_sq:.2f}]"
                
                print(f"\r左手: [{left_pos_safe[0]:+.3f}, {left_pos_safe[1]:+.3f}, {left_pos_safe[2]:+.3f}]  "
                      f"右手: [{right_pos_safe[0]:+.3f}, {right_pos_safe[1]:+.3f}, {right_pos_safe[2]:+.3f}]"
                      f"{gripper_info}", end='')
            
            # 控制频率
            elapsed = time.time() - loop_start
            if elapsed < dt:
                time.sleep(dt - elapsed)
                
    except KeyboardInterrupt:
        print("\n\n用户中断")
    finally:
        print("\n退出控制模式...")
        
        # 先停止视频接收，避免干扰
        if image_client:
            print("📷 停止图像客户端...")
            try:
                image_client.close()
            except Exception as e:
                # 忽略关闭时的ZMQ错误（正常现象）
                pass
        
        robot.set_ub_manip_mode(2)
        print("✅ Mode 2 (退出)")
        time.sleep(2)
        
        robot.enter_damping()
        print("✅ 阻尼模式")
        
        # 清理共享内存
        try:
            img_shm.close()
            img_shm.unlink()
        except Exception:
            pass
        
        print("👋 退出完成")


if __name__ == "__main__":
    main()

