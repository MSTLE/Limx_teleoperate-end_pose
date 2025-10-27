#!/usr/bin/env python3
"""
阶段1: WebSocket连接测试
目标: 确保能连接到机器人并接收消息
"""

import json
import time
import websocket

class SimpleRobotClient:
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        
    def on_message(self, ws, message):
        data = json.loads(message)
        
        # 获取机器人SN
        if 'accid' in data and not self.accid:
            self.accid = data['accid']
            print(f"✅ 机器人SN: {self.accid}")
        
        # 只打印非心跳消息
        if 'notify_robot_info' not in data.get('title', ''):
            print(f"📩 {data.get('title', 'unknown')}: {data.get('data', {}).get('result', '')}")
            
    def on_open(self, ws):
        print("✅ WebSocket已连接")
    
    def on_error(self, ws, error):
        print(f"❌ 错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 连接已关闭")
    
    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_open=self.on_open,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.run_forever()

if __name__ == "__main__":
    print("="*60)
    print("阶段1: WebSocket连接测试")
    print("="*60)
    print("\n⚠️  请确保:")
    print("1. 机器人已开机并悬挂 (脚离地≥15cm)")
    print("2. 已连接机器人WiFi (HU_D04_xxx, 密码: 12345678)")
    print("3. 遥控器在手边 (随时可按L2+X急停)")
    input("\n按Enter开始连接...")
    
    client = SimpleRobotClient()
    client.connect()

