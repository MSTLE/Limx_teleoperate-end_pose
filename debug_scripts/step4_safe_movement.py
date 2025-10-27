#!/usr/bin/env python3
"""
阶段4: 安全微小移动测试
目标: 用微小增量安全移动机械臂
策略: 固定基准位姿 + 微小偏移
"""

import json
import uuid
import time
import numpy as np
import websocket
from threading import Thread

class SafeRobotController:
    def __init__(self, robot_ip="10.192.1.2"):
        self.url = f"ws://{robot_ip}:5000"
        self.ws = None
        self.accid = None
        self.connected = False
        
        # 安全参数
        self.control_freq = 30  # Hz
        
        # ⚠️ 重要发现：API使用相对坐标系！
        # [0.0, 0.0, 0.0] = 相对于Mode 0初始姿态，零偏移（保持不动）
        # [0.01, 0.0, 0.0] = 相对于Mode 0初始姿态，X方向+1cm
        # 因此不需要绝对位姿，直接使用偏移量即可！
        self.base_left_pos = [0.0, 0.0, 0.0]     # 相对于Mode 0的零偏移
        self.base_left_quat = [0.0, 0.0, 0.0, 1.0]
        self.base_right_pos = [0.0, 0.0, 0.0]    # 相对于Mode 0的零偏移
        self.base_right_quat = [0.0, 0.0, 0.0, 1.0]
        
        # 工作空间限制（相对于Mode 0姿态的最大偏移）
        self.workspace = {
            'x_min': -0.10, 'x_max': 0.20,   # 前后移动范围 -10~+20cm
            'y_min': -0.15, 'y_max': 0.15,   # 左右移动范围 ±15cm
            'z_min': -0.15, 'z_max': 0.20    # 上下移动范围 -15~+20cm
        }
        
    def check_workspace(self, pos):
        """检查位置是否在安全工作空间内"""
        x, y, z = pos
        ws = self.workspace
        if not (ws['x_min'] <= x <= ws['x_max']):
            return False, f"X超限: {x:.3f} (范围 {ws['x_min']}-{ws['x_max']})"
        if not (ws['y_min'] <= y <= ws['y_max']):
            return False, f"Y超限: {y:.3f} (范围 {ws['y_min']}-{ws['y_max']})"
        if not (ws['z_min'] <= z <= ws['z_max']):
            return False, f"Z超限: {z:.3f} (范围 {ws['z_min']}-{ws['z_max']})"
        return True, "OK"
    
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
        
        # 打印响应
        if 'response_' in data.get('title', ''):
            if 'notify_robot_info' not in data.get('title', ''):
                result = data.get('data', {}).get('result', 'unknown')
                status = "✅" if result == "success" else "❌"
                print(f"{status} {data['title']}: {result}")
    
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
    
    def initialize(self):
        """初始化到操作模式"""
        print("\n🔄 初始化中...")
        self.send_request("request_damping")
        time.sleep(2)
        self.send_request("request_prepare")
        time.sleep(3)
        self.send_request("request_set_ub_manip_mode", {"mode": 0})
        time.sleep(4)
        self.send_request("request_set_ub_manip_mode", {"mode": 1})
        time.sleep(2)
        print("✅ 初始化完成")
    
    def shutdown(self):
        """安全关闭"""
        print("\n🔄 安全关闭中...")
        self.send_request("request_set_ub_manip_mode", {"mode": 2})
        time.sleep(4)
        self.send_request("request_damping")
        time.sleep(2)
        print("✅ 已关闭")
    
    def set_pose(self, left_pos, left_quat, right_pos, right_quat):
        """设置末端位姿（带安全检查）"""
        # 检查左手工作空间
        safe, msg = self.check_workspace(left_pos)
        if not safe:
            print(f"⚠️  左手{msg}，跳过此指令")
            return False
        
        # 检查右手工作空间
        safe, msg = self.check_workspace(right_pos)
        if not safe:
            print(f"⚠️  右手{msg}，跳过此指令")
            return False
        
        data = {
            "left_hand_pos": left_pos,
            "left_hand_quat": left_quat,
            "right_hand_pos": right_pos,
            "right_hand_quat": right_quat
        }
        self.send_request("request_set_ub_manip_ee_pose", data)
        return True
    
    def safe_move_smooth(self, target_left_offset, target_right_offset, duration=3.0):
        """
        🛡️ 平滑安全移动
        
        参数:
            target_left_offset: 左手位置偏移 [dx, dy, dz] (米)
            target_right_offset: 右手位置偏移 [dx, dy, dz] (米)
            duration: 移动时长(秒)
        """
        print(f"\n🎯 开始平滑移动 (时长{duration}秒)")
        
        left_offset = np.array(target_left_offset)
        right_offset = np.array(target_right_offset)
        
        # 检查移动距离
        left_dist = np.linalg.norm(left_offset)
        right_dist = np.linalg.norm(right_offset)
        max_dist = max(left_dist, right_dist)
        
        print(f"   左手移动: {left_dist*100:.2f}cm")
        print(f"   右手移动: {right_dist*100:.2f}cm")
        
        if max_dist > 0.15:  # 超过15cm
            print(f"❌ 移动距离过大: {max_dist*100:.1f}cm")
            return False
        
        # 计算插值步数
        num_steps = int(duration * self.control_freq)
        dt = duration / num_steps
        
        print(f"   插值步数: {num_steps}")
        print(f"   控制周期: {dt*1000:.1f}ms")
        
        # 执行插值移动
        for i in range(num_steps + 1):
            alpha = i / num_steps
            
            # 线性插值偏移
            current_left_offset = alpha * left_offset
            current_right_offset = alpha * right_offset
            
            # 计算目标位姿（基准 + 偏移）
            target_left_pos = (np.array(self.base_left_pos) + current_left_offset).tolist()
            target_right_pos = (np.array(self.base_right_pos) + current_right_offset).tolist()
            
            # 发送指令
            self.set_pose(
                target_left_pos,
                self.base_left_quat,
                target_right_pos,
                self.base_right_quat
            )
            
            # 进度显示
            if i % 10 == 0:
                progress = int(alpha * 20)
                bar = "█" * progress + "░" * (20 - progress)
                print(f"\r   进度: [{bar}] {alpha*100:.0f}%", end='', flush=True)
            
            time.sleep(dt)
        
        print("\n✅ 移动完成")
        return True

def test_safe_movement():
    """测试安全移动"""
    robot = SafeRobotController()
    
    print("="*60)
    print("阶段4: 安全微小移动测试")
    print("="*60)
    
    print("\n📐 安全工作空间限制:")
    ws = robot.workspace
    print(f"   X轴(前后): {ws['x_min']}m ~ {ws['x_max']}m")
    print(f"   Y轴(左右): {ws['y_min']}m ~ {ws['y_max']}m")
    print(f"   Z轴(上下): {ws['z_min']}m ~ {ws['z_max']}m")
    
    print("\n📍 基准位姿:")
    print(f"   左手: [{', '.join([f'{x:.2f}' for x in robot.base_left_pos])}]m")
    print(f"   右手: [{', '.join([f'{x:.2f}' for x in robot.base_right_pos])}]m")
    
    print("\n⚠️  安全检查:")
    print("□ 机器人已悬挂")
    print("□ 2米范围内无障碍物")
    print("□ 遥控器在手边 (L2+X急停)")
    print("□ 有人监控")
    input("\n✅ 确认后按Enter开始...")
    
    if not robot.connect():
        print("❌ 连接失败")
        return
    
    time.sleep(1)
    robot.initialize()
    
    print("\n⏸️  机器人已进入Mode 1状态")
    print("   ✅ 机器人已摆到默认姿态（肘部弯曲约65度）")
    print("   💡 我们将从这个姿态开始，只做微小的相对移动")
    print(f"   📍 理论基准位姿: 左{robot.base_left_pos} 右{robot.base_right_pos}")
    print("\n   🛡️ 安全策略: 先发送保持当前姿态的指令（零移动）")
    print("             然后再开始微小移动测试")
    input("\n✅ 按Enter继续...")
    
    print("\n" + "="*60)
    print("🧪 开始测试 - 微小移动")
    print("="*60)
    
    try:
        # 测试0: 零移动（保持当前姿态，激活系统）
        print("\n🧪 测试0: 零移动测试（保持当前姿态）")
        print("   目的: 激活位姿跟踪系统，机器人应该不动")
        print("   ⚠️  如果机器人突然移动，立即按L2+X急停！")
        input("按Enter开始...")
        robot.safe_move_smooth(
            [0.0, 0.0, 0.0],   # 左手零偏移
            [0.0, 0.0, 0.0],   # 右手零偏移
            duration=2.0
        )
        print("   ✅ 如果机器人没有移动，说明基准位姿设置正确")
        time.sleep(2)
        
        print("\n" + "-"*60)
        input("📍 零移动测试完成，按Enter继续微小移动测试...")
        
        # 测试1: 左手向前移动3cm
        print("\n🧪 测试1: 左手向前移动3cm")
        print("   观察动作是否平滑")
        input("按Enter开始...")
        robot.safe_move_smooth(
            [0.03, 0.0, 0.0],   # 左手 X+3cm
            [0.0, 0.0, 0.0],     # 右手不动
            duration=2.0  # 2秒完成
        )
        time.sleep(1)
        
        # 测试2: 回到基准位置
        print("\n🧪 测试2: 回到基准位置")
        input("按Enter开始...")
        robot.safe_move_smooth(
            [0.0, 0.0, 0.0],    # 回到基准
            [0.0, 0.0, 0.0],
            duration=2.0
        )
        time.sleep(1)
        
        print("\n✅ 前后移动测试完成！如果动作平滑，继续...")
        input("按Enter继续上下移动测试，或Ctrl+C退出...")
        
        # 测试3: 双手上移5cm
        print("\n🧪 测试3: 双手同时上移5cm")
        input("按Enter开始...")
        robot.safe_move_smooth(
            [0.0, 0.0, 0.05],   # 左手 Z+5cm
            [0.0, 0.0, 0.05],   # 右手 Z+5cm
            duration=2.0
        )
        time.sleep(1)
        
        # 测试4: 回到基准
        print("\n🧪 测试4: 回到基准位置")
        input("按Enter开始...")
        robot.safe_move_smooth(
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            duration=2.0
        )
        time.sleep(1)
        
        print("\n✅ 基础移动测试完成！如果都正常，继续组合测试...")
        input("按Enter继续，或Ctrl+C退出...")
        
        # 测试5: 左手左移+上移5cm
        print("\n🧪 测试5: 左手向左5cm+向上5cm")
        input("按Enter开始...")
        robot.safe_move_smooth(
            [0.0, 0.05, 0.05],   # 左手 Y+5cm, Z+5cm
            [0.0, 0.0, 0.0],     # 右手不动
            duration=3.0
        )
        time.sleep(1)
        
        # 最后回到基准
        print("\n🧪 最后: 回到基准位置")
        robot.safe_move_smooth(
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            duration=3.0
        )
        
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断")
    finally:
        robot.shutdown()
    
    print("\n✅ 所有测试完成!")

if __name__ == "__main__":
    test_safe_movement()

