#!/usr/bin/env python3
"""
Step 7: Quest VR实时控制机器人 (使用原版TeleVuerWrapper)

安全说明:
1. 机器人必须悬挂，脚离地≥15cm
2. 控制范围限制在±20cm以内
3. 遥控器在手边随时可按L2+X急停
4. 使用相对坐标系，[0,0,0]为零偏移，相对于Mode 1初始姿态
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


class RobotController:
    """机器人控制器"""
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
        # ⚠️ 重要：API使用相对坐标系！
        # [0.0, 0.0, 0.0] = 相对于Mode 0初始姿态，零偏移
        self.base_left_pos = [0.0, 0.0, 0.0]
        self.base_left_quat = [0.0, 0.0, 0.0, 1.0]
        self.base_right_pos = [0.0, 0.0, 0.0]
        self.base_right_quat = [0.0, 0.0, 0.0, 1.0]
        
        # 工作空间限制（相对偏移的最大值）
        self.workspace = {
            'x_min': -0.10, 'x_max': 0.20,
            'y_min': -0.15, 'y_max': 0.15,
            'z_min': -0.15, 'z_max': 0.20
        }
        
        self.max_velocity = 0.15  # m/s
        
    def on_message(self, ws, message):
        data = json.loads(message)
        if 'accid' in data and not self.accid:
            self.accid = data['accid']
            print(f"✅ 已连接: {self.accid}")
        
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
            
        # 等待accid
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
        
    def enter_damping(self):
        """进入阻尼模式"""
        self.send_command("request_damping")
        time.sleep(2)
        
    def enter_prepare(self):
        """进入准备模式"""
        self.send_command("request_prepare")
        time.sleep(3)
        
    def set_ub_manip_mode(self, mode):
        """设置上肢操作模式 (0/1/2)"""
        self.send_command("request_set_ub_manip_mode", {"mode": mode})
        time.sleep(3 if mode in [0, 2] else 1)
        
    def set_pose(self, left_pos, left_quat, right_pos, right_quat, head_quat=None):
        """设置机器人位姿（相对坐标）"""
        data = {
            "head_quat": head_quat or [0.0, 0.0, 0.0, 1.0],
            "left_hand_pos": left_pos,
            "left_hand_quat": left_quat,
            "right_hand_pos": right_pos,
            "right_hand_quat": right_quat
        }
        self.send_command("request_set_ub_manip_ee_pose", data)
        
    def clip_to_workspace(self, offset):
        """限制偏移量到安全范围"""
        return [
            np.clip(offset[0], self.workspace['x_min'], self.workspace['x_max']),
            np.clip(offset[1], self.workspace['y_min'], self.workspace['y_max']),
            np.clip(offset[2], self.workspace['z_min'], self.workspace['z_max'])
        ]


def matrix_to_pos_quat(matrix):
    """从4x4矩阵提取位置和四元数"""
    pos = matrix[:3, 3].tolist()
    
    # 旋转矩阵转四元数
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


def save_calibration(calib_left, calib_right, filename="vr_calibration.pkl"):
    """保存标定数据"""
    calib_data = {
        'calib_left': calib_left,
        'calib_right': calib_right,
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
        
        # 显示标定信息
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(calib_data['timestamp']))
        print(f"\n📂 找到标定文件:")
        print(f"   保存时间: {timestamp}")
        print(f"   左手参考: {calib_data['calib_left'][:3, 3]}")
        print(f"   右手参考: {calib_data['calib_right'][:3, 3]}")
        
        return calib_data['calib_left'], calib_data['calib_right']
    except Exception as e:
        print(f"❌ 加载标定失败: {e}")
        return None


def calibrate_vr(tv_wrapper):
    """执行VR标定"""
    print("📊 开始采集标定数据（保持双手不动）...")
    
    calibration_samples = []
    print("   标定中", end='', flush=True)
    for i in range(30):  # 1秒采样30次
        tele_data = tv_wrapper.get_motion_state_data()
        calibration_samples.append({
            'left': tele_data.left_arm_pose.copy(),
            'right': tele_data.right_arm_pose.copy()
        })
        time.sleep(1/30)
        if (i+1) % 10 == 0:
            print(".", end='', flush=True)
    
    # 计算标定偏移（平均值）
    calib_left = np.mean([s['left'] for s in calibration_samples], axis=0)
    calib_right = np.mean([s['right'] for s in calibration_samples], axis=0)
    
    print(" 完成!")
    print(f"\n✅ 标定成功!")
    print(f"   左手参考位置: {calib_left[:3, 3]}")
    print(f"   右手参考位置: {calib_right[:3, 3]}")
    
    return calib_left, calib_right


def main():
    print("="*60)
    print("Step 7: Meta Quest VR实时控制")
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
    # 创建虚拟图像共享内存（TeleVuerWrapper需要）
    img_shape = (480, 640, 3)
    img_shm = shared_memory.SharedMemory(create=True, size=np.prod(img_shape) * np.uint8().itemsize)
    img_array = np.ndarray(img_shape, dtype=np.uint8, buffer=img_shm.buf)
    img_array[:] = 128  # 灰色背景
    
    # 选择模式
    print("\n选择输入模式:")
    print("1. 手柄控制器 (controller)")
    print("2. 手部追踪 (hand tracking)")
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
    print(f"   模式: {'手部追踪' if use_hand_tracking else '手柄控制器'}")
    print(f"\n📱 在Quest中打开浏览器，访问:")
    print(f"   https://vuer.ai?grid=False")
    print(f"   (或者显示的具体地址)")
    input("\n等待Quest连接后按Enter开始初始化机器人...")
    
    # 连接机器人
    print("\n连接机器人...")
    robot = RobotController()
    robot.connect()
    
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
    
    # 标定VR坐标系（每次都重新标定）
    print("\n"+"="*60)
    print("🎯 标定阶段")
    print("="*60)
    
    # 5秒倒计时准备
    print("\n⏱️  准备标定，倒计时...")
    print("   请将双手移动到舒适的起始位置")
    for i in range(5, 0, -1):
        print(f"   {i}...", flush=True)
        time.sleep(1)
    print("   ✅ 时间到!\n")
    
    # 执行标定
    calib_left, calib_right = calibrate_vr(tv_wrapper)
    save_calibration(calib_left, calib_right)
    
    # 主控制循环
    print("\n"+"="*60)
    print("🤖 开始控制! (Ctrl+C退出)")
    print("="*60)
    print()
    
    try:
        control_rate = 30  # Hz
        dt = 1.0 / control_rate
        
        while True:
            loop_start = time.time()
            
            # 获取VR数据
            tele_data = tv_wrapper.get_motion_state_data()
            
            # 计算相对偏移
            left_offset = (tele_data.left_arm_pose[:3, 3] - calib_left[:3, 3]).tolist()
            right_offset = (tele_data.right_arm_pose[:3, 3] - calib_right[:3, 3]).tolist()
            
            # 限制到安全范围
            left_offset_safe = robot.clip_to_workspace(left_offset)
            right_offset_safe = robot.clip_to_workspace(right_offset)
            
            # 提取四元数
            _, left_quat = matrix_to_pos_quat(tele_data.left_arm_pose)
            _, right_quat = matrix_to_pos_quat(tele_data.right_arm_pose)
            
            # 发送到机器人（相对坐标）
            robot.set_pose(
                left_pos=left_offset_safe,
                left_quat=left_quat,
                right_pos=right_offset_safe,
                right_quat=right_quat
            )
            
            # 打印状态（每秒1次）
            if int(time.time() * 1) % 1 == 0:
                print(f"\r左: [{left_offset_safe[0]:+.3f}, {left_offset_safe[1]:+.3f}, {left_offset_safe[2]:+.3f}]  "
                      f"右: [{right_offset_safe[0]:+.3f}, {right_offset_safe[1]:+.3f}, {right_offset_safe[2]:+.3f}]", end='')
            
            # 控制频率
            elapsed = time.time() - loop_start
            if elapsed < dt:
                time.sleep(dt - elapsed)
                
    except KeyboardInterrupt:
        print("\n\n用户中断")
    finally:
        print("\n退出控制模式...")
        robot.set_ub_manip_mode(2)
        print("✅ Mode 2 (退出)")
        time.sleep(2)
        
        robot.enter_damping()
        print("✅ 阻尼模式")
        
        # 清理
        img_shm.close()
        img_shm.unlink()
        print("👋 退出完成")


if __name__ == "__main__":
    main()
