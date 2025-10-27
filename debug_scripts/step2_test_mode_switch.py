#!/usr/bin/env python3
"""
阶段2: 模式切换测试
目标: 验证基本控制指令 (阻尼/准备/移动操作模式)
"""

import json
import uuid
import time
import websocket
from threading import Thread

class RobotController:
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
    def send_request(self, title, data=None):
        """发送请求"""
        if not self.connected:
            print("❌ 未连接")
            return
            
        msg = {
            "accid": self.accid,
            "title": title,
            "timestamp": int(time.time() * 1000),
            "guid": str(uuid.uuid4()),
            "data": data or {}
        }
        
        self.ws.send(json.dumps(msg))
        print(f"📤 发送: {title}")
    
    def on_message(self, ws, message):
        data = json.loads(message)
        
        if not self.accid and 'accid' in data:
            self.accid = data['accid']
            print(f"✅ 已连接: {self.accid}")
        
        # 打印响应和通知（过滤心跳）
        if 'response_' in data.get('title', '') or 'notify_' in data.get('title', ''):
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
        
        # 等待连接
        for i in range(50):
            if self.connected and self.accid:
                return True
            time.sleep(0.1)
        return False
    
    # ===== 控制方法 =====
    
    def enter_damping(self):
        """进入阻尼模式"""
        self.send_request("request_damping")
    
    def enter_prepare(self):
        """进入准备模式"""
        self.send_request("request_prepare")
    
    def set_ub_manip_mode(self, mode):
        """设置移动操作模式 (0/1/2)"""
        self.send_request("request_set_ub_manip_mode", {"mode": mode})

def safe_test_sequence(robot):
    """安全测试序列"""
    
    print("\n" + "="*60)
    print("🧪 测试序列开始")
    print("="*60)
    
    # 1. 阻尼模式
    print("\n1️⃣  测试: 进入阻尼模式")
    print("   期望: 机器人关节可手动掰动")
    robot.enter_damping()
    time.sleep(2)
    input("   ✅ 请手动掰动关节验证，按Enter继续...")
    
    # 2. 准备模式
    print("\n2️⃣  测试: 进入准备模式")
    print("   期望: 机器人站直，关节带力")
    robot.enter_prepare()
    time.sleep(3)
    input("   ✅ 验证机器人姿态，按Enter继续...")
    
    # 3. 移动操作 Mode 0
    print("\n3️⃣  测试: 移动操作 Mode 0 (准备进入)")
    print("   期望: 机器人双臂缓慢移动到初始位置")
    robot.set_ub_manip_mode(0)
    time.sleep(4)
    input("   ✅ 验证双臂姿态，按Enter继续...")
    
    # 4. 移动操作 Mode 1
    print("\n4️⃣  测试: 移动操作 Mode 1 (激活)")
    print("   ⚠️  注意: 此时机器人等待位姿指令")
    robot.set_ub_manip_mode(1)
    time.sleep(2)
    print("   ⏸️  保持此模式，准备进入下一阶段")
    input("   按Enter继续...")
    
    # 5. 移动操作 Mode 2
    print("\n5️⃣  测试: 移动操作 Mode 2 (退出)")
    print("   期望: 机器人双臂缓慢回到初始位置")
    robot.set_ub_manip_mode(2)
    time.sleep(4)
    
    # 6. 回到阻尼
    print("\n6️⃣  测试: 回到阻尼模式")
    robot.enter_damping()
    time.sleep(2)
    
    print("\n✅ 测试序列完成!")

if __name__ == "__main__":
    print("="*60)
    print("阶段2: 模式切换测试")
    print("="*60)
    print("\n⚠️  安全检查:")
    print("□ 机器人已悬挂，脚离地≥15cm")
    print("□ 2米范围内无障碍物")
    print("□ 遥控器在手边")
    print("□ 有人监控机器人")
    input("\n✅ 确认后按Enter开始...")
    
    robot = RobotController()
    
    if not robot.connect():
        print("❌ 连接失败")
        exit(1)
    
    time.sleep(1)
    
    try:
        safe_test_sequence(robot)
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
        robot.enter_damping()
    
    print("\n👋 测试结束")

