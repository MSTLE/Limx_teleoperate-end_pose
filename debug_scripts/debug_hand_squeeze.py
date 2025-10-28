#!/usr/bin/env python3
"""
手部握紧检测调试脚本

用于诊断手部追踪的squeeze值是否正常工作。
不连接机器人，只显示VR手部数据。
"""

import numpy as np
import time
from multiprocessing import shared_memory
from televuer.tv_wrapper import TeleVuerWrapper
from pathlib import Path


def main():
    print("="*60)
    print("手部握紧检测调试")
    print("="*60)
    
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
    img_array[:] = 128
    
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
    input("\n等待Quest连接后按Enter开始监控...")
    
    print("\n"+"="*60)
    print("开始监控手部数据")
    print("="*60)
    print()
    
    if use_hand_tracking:
        print("📋 手部追踪说明:")
        print("  - 张开双手，观察 squeeze_value 应接近 0.0")
        print("  - 握紧拳头，观察 squeeze_value 应接近 1.0")
        print("  - 食指和拇指捏合，观察 pinch_value 应接近 0.0")
        print("  - squeeze_state/pinch_state: 布尔值，表示是否激活")
    else:
        print("📋 手柄控制器说明:")
        print("  - 松开握把(Grip)，观察 squeeze_ctrl_value 应接近 0.0")
        print("  - 按紧握把(Grip)，观察 squeeze_ctrl_value 应接近 1.0")
        print("  - trigger_value: 扳机拉动深度")
    
    print("\n按 Ctrl+C 退出\n")
    
    try:
        while True:
            time.sleep(0.1)  # 10Hz更新
            
            # 获取VR数据
            tele_data = tv_wrapper.get_motion_state_data()
            
            if not tele_data.tele_state:
                print("\r⚠️  等待VR数据...", end='', flush=True)
                continue
            
            if use_hand_tracking:
                # 手部追踪模式
                state = tele_data.tele_state
                
                # 详细信息
                print(f"\r左手: squeeze={state.left_squeeze_value:.3f} "
                      f"pinch={tele_data.left_pinch_value/100:.3f} "
                      f"[状态: squeeze={state.left_squeeze_state} pinch={state.left_pinch_state}]  |  "
                      f"右手: squeeze={state.right_squeeze_value:.3f} "
                      f"pinch={tele_data.right_pinch_value/100:.3f} "
                      f"[状态: squeeze={state.right_squeeze_state} pinch={state.right_pinch_state}]",
                      end='', flush=True)
                
                # 计算夹爪映射（使用squeeze）
                left_gripper_sq = int((1.0 - state.left_squeeze_value) * 1000)
                right_gripper_sq = int((1.0 - state.right_squeeze_value) * 1000)
                
                # 计算夹爪映射（使用pinch）
                left_gripper_pi = int((tele_data.left_pinch_value / 100.0) * 1000)
                right_gripper_pi = int((tele_data.right_pinch_value / 100.0) * 1000)
                
                # 每2秒打印详细信息
                if int(time.time() * 0.5) % 2 == 0:
                    print()
                    print(f"  → 使用squeeze映射: 夹爪 L:{left_gripper_sq:4d} R:{right_gripper_sq:4d}")
                    print(f"  → 使用pinch映射:   夹爪 L:{left_gripper_pi:4d} R:{right_gripper_pi:4d}")
                    print()
                    
            else:
                # 手柄控制器模式
                state = tele_data.tele_state
                
                print(f"\r左手柄: Grip={state.left_squeeze_ctrl_value:.3f} "
                      f"Trigger={tele_data.left_trigger_value/10:.3f} "
                      f"[按下: Grip={state.left_squeeze_ctrl_state} Trigger={state.left_trigger_state}]  |  "
                      f"右手柄: Grip={state.right_squeeze_ctrl_value:.3f} "
                      f"Trigger={tele_data.right_trigger_value/10:.3f} "
                      f"[按下: Grip={state.right_squeeze_ctrl_state} Trigger={state.right_trigger_state}]",
                      end='', flush=True)
                
                # 计算夹爪映射
                left_gripper = int((1.0 - state.left_squeeze_ctrl_value) * 1000)
                right_gripper = int((1.0 - state.right_squeeze_ctrl_value) * 1000)
                
                if int(time.time() * 0.5) % 2 == 0:
                    print()
                    print(f"  → 夹爪映射: L:{left_gripper:4d} R:{right_gripper:4d}")
                    print()
                
    except KeyboardInterrupt:
        print("\n\n用户中断")
    finally:
        # 清理
        img_shm.close()
        img_shm.unlink()
        print("👋 退出")


if __name__ == "__main__":
    main()

