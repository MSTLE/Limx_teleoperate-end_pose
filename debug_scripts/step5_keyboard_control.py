#!/usr/bin/env python3
"""
阶段5: 键盘实时控制测试
目标: 验证实时位姿控制逻辑，为VR控制做准备
"""

import json
import uuid
import time
import numpy as np
import websocket
from threading import Thread
import sys
import tty
import termios

class KeyboardRobotController:
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
        # 控制参数
        self.control_freq = 30  # Hz
        self.running = False
        
        # 当前位姿偏移（相对于Mode 0初始姿态）
        self.left_offset = np.array([0.0, 0.0, 0.0])
        self.right_offset = np.array([0.0, 0.0, 0.0])
        
        # 移动步长
        self.step_size = 0.01  # 每次按键移动1cm
        
        # 工作空间限制
        self.workspace = {
            'x_min': -0.10, 'x_max': 0.20,
            'y_min': -0.15, 'y_max': 0.15,
            'z_min': -0.15, 'z_max': 0.20
        }
    
    def check_workspace(self, offset):
        """检查偏移是否在安全范围内"""
        x, y, z = offset
        ws = self.workspace
        x = np.clip(x, ws['x_min'], ws['x_max'])
        y = np.clip(y, ws['y_min'], ws['y_max'])
        z = np.clip(z, ws['z_min'], ws['z_max'])
        return np.array([x, y, z])
    
    def send_request(self, title, data=None):
        msg = {
            "accid": self.accid,
            "title": title,
            "timestamp": int(time.time() * 1000),
            "guid": str(uuid.uuid4()),
            "data": data or {}
        }
        self.ws.send(json.dumps(msg))
    
    def on_message(self, ws, message):
        data = json.loads(message)
        
        if not self.accid and 'accid' in data:
            self.accid = data['accid']
            print(f"✅ 已连接: {self.accid}")
        
        # 只打印错误或重要消息
        title = data.get('title', '')
        if 'response_' in title:
            result = data.get('data', {}).get('result', '')
            if result != 'success':
                print(f"⚠️  {title}: {result}")
    
    def on_open(self, ws):
        print("✅ WebSocket已连接")
    
    def on_error(self, ws, error):
        print(f"❌ 错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 连接已关闭")
        self.running = False
    
    def connect(self):
        print("连接中...")
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        thread = Thread(target=self.ws.run_forever, daemon=True)
        thread.start()
        
        time.sleep(2)
        return self.accid is not None
    
    def initialize(self):
        """初始化到Mode 1"""
        print("\n初始化机器人...")
        self.send_request("request_damping")
        time.sleep(2)
        self.send_request("request_prepare")
        time.sleep(3)
        self.send_request("request_set_ub_manip_mode", {"mode": 0})
        time.sleep(3)
        self.send_request("request_set_ub_manip_mode", {"mode": 1})
        time.sleep(2)
        print("✅ 已进入Mode 1")
    
    def send_pose(self):
        """发送当前位姿"""
        data = {
            "left_hand_pos": self.left_offset.tolist(),
            "left_hand_quat": [0.0, 0.0, 0.0, 1.0],
            "right_hand_pos": self.right_offset.tolist(),
            "right_hand_quat": [0.0, 0.0, 0.0, 1.0]
        }
        self.send_request("request_set_ub_manip_ee_pose", data)
    
    def control_loop(self):
        """实时控制循环（30Hz）"""
        self.running = True
        dt = 1.0 / self.control_freq
        
        while self.running:
            self.send_pose()
            time.sleep(dt)
    
    def shutdown(self):
        """安全关闭"""
        print("\n🔄 安全关闭中...")
        self.running = False
        time.sleep(0.5)
        self.send_request("request_set_ub_manip_mode", {"mode": 2})
        time.sleep(3)
        self.send_request("request_damping")
        time.sleep(2)
        print("✅ 已关闭")


def get_key():
    """获取单个按键（非阻塞）"""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def keyboard_control():
    """键盘控制主程序"""
    robot = KeyboardRobotController()
    
    print("="*60)
    print("阶段5: 键盘实时控制测试")
    print("="*60)
    
    print("\n⚠️  请确保:")
    print("□ 机器人已悬挂")
    print("□ 遥控器在手边")
    input("\n✅ 确认后按Enter开始...")
    
    if not robot.connect():
        print("❌ 连接失败")
        return
    
    time.sleep(1)
    robot.initialize()
    
    # 启动控制循环
    control_thread = Thread(target=robot.control_loop, daemon=True)
    control_thread.start()
    
    print("\n" + "="*60)
    print("🎮 键盘控制已激活 (30Hz实时发送)")
    print("="*60)
    print("\n控制说明:")
    print("  左手控制:")
    print("    w/s - 前进/后退")
    print("    a/d - 左移/右移")
    print("    q/e - 上升/下降")
    print("\n  右手控制:")
    print("    i/k - 前进/后退")
    print("    j/l - 左移/右移")
    print("    u/o - 上升/下降")
    print("\n  其他:")
    print("    r   - 重置到零位")
    print("    ESC - 退出")
    print("\n" + "="*60)
    
    try:
        while robot.running:
            key = get_key()
            
            if key == '\x1b':  # ESC
                print("\n退出控制...")
                break
            
            # 左手控制
            elif key == 'w':
                robot.left_offset[0] += robot.step_size  # 前进
            elif key == 's':
                robot.left_offset[0] -= robot.step_size  # 后退
            elif key == 'a':
                robot.left_offset[1] += robot.step_size  # 左移
            elif key == 'd':
                robot.left_offset[1] -= robot.step_size  # 右移
            elif key == 'q':
                robot.left_offset[2] += robot.step_size  # 上升
            elif key == 'e':
                robot.left_offset[2] -= robot.step_size  # 下降
            
            # 右手控制
            elif key == 'i':
                robot.right_offset[0] += robot.step_size
            elif key == 'k':
                robot.right_offset[0] -= robot.step_size
            elif key == 'j':
                robot.right_offset[1] += robot.step_size
            elif key == 'l':
                robot.right_offset[1] -= robot.step_size
            elif key == 'u':
                robot.right_offset[2] += robot.step_size
            elif key == 'o':
                robot.right_offset[2] -= robot.step_size
            
            # 重置
            elif key == 'r':
                robot.left_offset = np.array([0.0, 0.0, 0.0])
                robot.right_offset = np.array([0.0, 0.0, 0.0])
                print("\n🔄 重置到零位")
            
            # 限位保护
            robot.left_offset = robot.check_workspace(robot.left_offset)
            robot.right_offset = robot.check_workspace(robot.right_offset)
            
            # 显示当前位置
            print(f"\r左手: [{robot.left_offset[0]:+.3f}, {robot.left_offset[1]:+.3f}, {robot.left_offset[2]:+.3f}]  "
                  f"右手: [{robot.right_offset[0]:+.3f}, {robot.right_offset[1]:+.3f}, {robot.right_offset[2]:+.3f}]  ", 
                  end='', flush=True)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    finally:
        robot.shutdown()
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    keyboard_control()

