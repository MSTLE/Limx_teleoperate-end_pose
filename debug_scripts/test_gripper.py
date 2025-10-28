#!/usr/bin/env python3
"""
夹爪控制测试脚本

用于单独测试夹爪控制功能，无需VR设备。
测试夹爪从完全张开到完全闭合，再返回张开状态。
"""

import json
import time
import threading
import websocket
import uuid


class SimpleRobotController:
    """简单的机器人控制器（仅用于测试夹爪）"""
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
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
        
    def set_gripper(self, left_opening=None, right_opening=None, speed=500, force=300):
        """
        控制夹爪开口度
        
        Args:
            left_opening: 左夹爪开口度 [0, 1000]
            right_opening: 右夹爪开口度 [0, 1000]
            speed: 夹爪速度 [0, 1000]
            force: 夹爪力度 [0, 1000]
        """
        data = {}
        
        if left_opening is not None:
            data["left_opening"] = int(left_opening)
            data["left_speed"] = speed
            data["left_force"] = force
            data["left_mode"] = 3  # 位控模式
        
        if right_opening is not None:
            data["right_opening"] = int(right_opening)
            data["right_speed"] = speed
            data["right_force"] = force
            data["right_mode"] = 3  # 位控模式
        
        if data:
            self.send_command("request_set_claw_cmd", data)
            print(f"📤 发送夹爪命令: L={left_opening}, R={right_opening}")


def main():
    print("="*60)
    print("夹爪控制测试")
    print("="*60)
    print("\n⚠️  注意:")
    print("1. 确保机器人已开机")
    print("2. 确保机器人装有因时二指夹爪")
    print("3. 机器人应处于阻尼模式或准备模式")
    input("\n✅ 确认后按Enter开始测试...")
    
    # 连接机器人
    print("\n连接机器人...")
    robot = SimpleRobotController()
    robot.connect()
    print("✅ 连接成功")
    
    print("\n"+"="*60)
    print("开始测试夹爪")
    print("="*60)
    
    try:
        # 测试序列
        tests = [
            (1000, "完全张开"),
            (750, "75% 张开"),
            (500, "50% 张开"),
            (250, "25% 张开"),
            (0, "完全闭合"),
            (500, "50% 张开"),
            (1000, "完全张开"),
        ]
        
        for opening, description in tests:
            print(f"\n{description}: {opening}/1000")
            robot.set_gripper(left_opening=opening, right_opening=opening)
            time.sleep(2)  # 等待夹爪移动到位
        
        print("\n"+"="*60)
        print("✅ 测试完成！")
        print("="*60)
        
        # 询问是否进行手动控制
        print("\n是否进入手动控制模式？(y/n): ", end='')
        choice = input().strip().lower()
        
        if choice == 'y':
            print("\n进入手动控制模式")
            print("输入开口度 (0-1000)，或输入 'q' 退出")
            print("格式: 左夹爪,右夹爪  例如: 500,500")
            print("     或者只输入一个数字控制两侧: 500")
            
            while True:
                try:
                    user_input = input("\n开口度> ").strip()
                    if user_input.lower() == 'q':
                        break
                    
                    if ',' in user_input:
                        left, right = map(int, user_input.split(','))
                    else:
                        left = right = int(user_input)
                    
                    if 0 <= left <= 1000 and 0 <= right <= 1000:
                        robot.set_gripper(left_opening=left, right_opening=right)
                    else:
                        print("❌ 数值必须在 0-1000 范围内")
                        
                except ValueError:
                    print("❌ 输入格式错误")
                except KeyboardInterrupt:
                    break
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
    finally:
        print("\n👋 退出")


if __name__ == "__main__":
    main()

