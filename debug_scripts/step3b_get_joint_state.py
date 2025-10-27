#!/usr/bin/env python3
"""
阶段3b: 读取关节状态
目标: 获取Mode 1时的默认关节位置，用于设置安全的基准位姿
"""

import json
import uuid
import time
import websocket
from threading import Thread, Event

class JointStateReader:
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
        # 关节状态数据
        self.joint_state = None
        self.joint_received = Event()
        
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
        
        title = data.get('title', '')
        
        # 处理关节状态响应
        if 'response_get_joint_state' in title:
            result = data.get('data', {}).get('result', 'unknown')
            if result == 'success':
                self.joint_state = data['data']
                self.joint_received.set()
                print("📩 收到关节状态数据")
            else:
                print(f"❌ 获取关节状态失败: {result}")
                self.joint_received.set()
        
        # 打印其他响应
        elif 'response_' in title:
            result = data.get('data', {}).get('result', 'unknown')
            print(f"📩 {title} -> {result}")
    
    def on_open(self, ws):
        print("✅ WebSocket已连接")
    
    def on_error(self, ws, error):
        print(f"❌ 错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 连接已关闭")
    
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
        
        # 等待连接
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
    
    def get_joint_state(self, timeout=3.0):
        """获取关节状态"""
        self.joint_received.clear()
        self.send_request("request_get_joint_state")
        
        if self.joint_received.wait(timeout):
            return self.joint_state
        else:
            print("❌ 获取关节状态超时")
            return None
    
    def shutdown(self):
        """安全关闭"""
        print("\n🔄 安全关闭中...")
        self.send_request("request_set_ub_manip_mode", {"mode": 2})
        time.sleep(3)
        self.send_request("request_damping")
        time.sleep(2)
        print("✅ 已关闭")

def test_joint_state():
    """测试关节状态读取"""
    robot = JointStateReader()
    
    print("="*60)
    print("阶段3b: 关节状态读取测试")
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
    
    print("\n" + "="*60)
    print("🧪 读取Mode 1时的关节状态")
    print("="*60)
    
    try:
        # 读取关节状态
        print("\n📍 正在读取关节状态...")
        joint_state = robot.get_joint_state()
        
        if joint_state and joint_state.get('result') == 'success':
            names = joint_state.get('names', [])
            positions = joint_state.get('q', [])
            velocities = joint_state.get('dq', [])
            torques = joint_state.get('tau', [])
            
            print(f"\n✅ 成功读取 {len(names)} 个关节的状态\n")
            
            # 找到双臂关节
            left_arm_joints = []
            right_arm_joints = []
            
            for i, name in enumerate(names):
                if 'left_shoulder' in name or 'left_elbow' in name or 'left_wrist' in name:
                    left_arm_joints.append((name, positions[i]))
                elif 'right_shoulder' in name or 'right_elbow' in name or 'right_wrist' in name:
                    right_arm_joints.append((name, positions[i]))
            
            print("📊 左臂关节位置 (弧度):")
            print("-" * 60)
            for name, pos in left_arm_joints:
                print(f"  {name:30s}: {pos:8.4f} rad ({pos*57.3:.1f}°)")
            
            print("\n📊 右臂关节位置 (弧度):")
            print("-" * 60)
            for name, pos in right_arm_joints:
                print(f"  {name:30s}: {pos:8.4f} rad ({pos*57.3:.1f}°)")
            
            print("\n" + "="*60)
            print("📋 完整关节列表:")
            print("="*60)
            for i, name in enumerate(names):
                pos = positions[i]
                vel = velocities[i] if i < len(velocities) else 0
                tau = torques[i] if i < len(torques) else 0
                print(f"{i+1:2d}. {name:30s} | pos: {pos:7.4f} | vel: {vel:7.4f} | tau: {tau:7.2f}")
            
            # 保存到文件
            output_file = "/home/wxp/project/LIMX/Limx_teleoperate-end_pose/debug_scripts/joint_state_mode1.json"
            with open(output_file, 'w') as f:
                json.dump(joint_state, f, indent=2)
            print(f"\n💾 关节状态已保存到: {output_file}")
            
        else:
            print("❌ 未能获取关节状态")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    finally:
        robot.shutdown()
    
    print("\n✅ 测试完成!")

if __name__ == "__main__":
    test_joint_state()

