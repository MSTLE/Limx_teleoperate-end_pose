#!/usr/bin/env python3
"""
阶段3: 读取机器人位姿
目标: 能够获取当前末端位姿数据
"""

import json
import uuid
import time
import websocket
from threading import Thread, Event

class RobotPoseReader:
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
        # 位姿数据
        self.current_pose = None
        self.pose_received = Event()
        
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
        
        # 处理位姿响应
        if data.get('title') == 'response_get_ub_manip_ee_pose':
            result = data.get('data', {}).get('result')
            if result == 'success':
                self.current_pose = data['data']
                self.pose_received.set()
                print("✅ 收到位姿数据")
            else:
                print(f"❌ 获取位姿失败: {result}")
        
        # 打印其他响应
        elif 'response_' in data.get('title', ''):
            if 'notify_robot_info' not in data.get('title', ''):
                result = data.get('data', {}).get('result', 'unknown')
                print(f"📩 {data['title']} -> {result}")
    
    def on_open(self, ws):
        self.connected = True
        print("✅ WebSocket已连接")
    
    def on_error(self, ws, error):
        print(f"❌ 错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 连接已关闭")
        self.connected = False
    
    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_open=self.on_open,
            on_error=self.on_error,
            on_close=self.on_close
        )
        Thread(target=self.ws.run_forever, daemon=True).start()
        
        for i in range(50):
            if self.connected and self.accid:
                return True
            time.sleep(0.1)
        return False
    
    def enter_damping(self):
        self.send_request("request_damping")
        time.sleep(2)
    
    def enter_prepare(self):
        self.send_request("request_prepare")
        time.sleep(3)
    
    def set_ub_manip_mode(self, mode):
        self.send_request("request_set_ub_manip_mode", {"mode": mode})
        time.sleep(3 if mode != 1 else 2)
    
    def get_current_pose(self, timeout=3.0):
        """获取当前末端位姿"""
        self.pose_received.clear()
        self.send_request("request_get_ub_manip_ee_pose")
        
        if self.pose_received.wait(timeout):
            return self.current_pose
        else:
            print("❌ 获取位姿超时")
            return None
    
    def set_pose(self, left_pos, left_quat, right_pos, right_quat):
        """设置末端位姿"""
        data = {
            "left_hand_pos": left_pos,
            "left_hand_quat": left_quat,
            "right_hand_pos": right_pos,
            "right_hand_quat": right_quat
        }
        self.send_request("request_set_ub_manip_ee_pose", data)

def test_pose_reading():
    robot = RobotPoseReader()
    
    print("连接中...")
    if not robot.connect():
        print("❌ 连接失败")
        return
    
    time.sleep(1)
    
    print("\n初始化机器人...")
    robot.enter_damping()
    robot.enter_prepare()
    robot.set_ub_manip_mode(0)
    robot.set_ub_manip_mode(1)
    
    print("\n发送初始位姿指令（激活位姿跟踪）...")
    # 发送一个默认位姿来激活系统
    robot.set_pose(
        [0.3, 0.3, 0.8],      # 左手位置
        [0.0, 0.0, 0.0, 1.0], # 左手姿态
        [0.3, -0.3, 0.8],     # 右手位置
        [0.0, 0.0, 0.0, 1.0]  # 右手姿态
    )
    print("等待5秒让系统稳定...")
    time.sleep(5)
    
    print("\n" + "="*60)
    print("🧪 位姿读取测试 - 连续读取10次")
    print("="*60)
    
    # 连续读取10次
    for i in range(10):
        print(f"\n📍 读取 #{i+1}")
        pose = robot.get_current_pose()
        
        if pose:
            left_pos = pose.get('left_hand_pos', [])
            left_quat = pose.get('left_hand_quat', [])
            right_pos = pose.get('right_hand_pos', [])
            right_quat = pose.get('right_hand_quat', [])
            
            print(f"  左手位置: [{left_pos[0]:.4f}, {left_pos[1]:.4f}, {left_pos[2]:.4f}]")
            print(f"  左手姿态: [{left_quat[0]:.4f}, {left_quat[1]:.4f}, {left_quat[2]:.4f}, {left_quat[3]:.4f}]")
            print(f"  右手位置: [{right_pos[0]:.4f}, {right_pos[1]:.4f}, {right_pos[2]:.4f}]")
            print(f"  右手姿态: [{right_quat[0]:.4f}, {right_quat[1]:.4f}, {right_quat[2]:.4f}, {right_quat[3]:.4f}]")
        
        time.sleep(0.5)
    
    print("\n退出移动操作模式...")
    robot.set_ub_manip_mode(2)
    robot.enter_damping()
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    print("="*60)
    print("阶段3: 位姿读取测试")
    print("="*60)
    print("\n⚠️  请确保:")
    print("□ 机器人已悬挂")
    print("□ 遥控器在手边")
    input("\n✅ 确认后按Enter开始...")
    
    try:
        test_pose_reading()
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    
    print("\n👋 测试结束")

