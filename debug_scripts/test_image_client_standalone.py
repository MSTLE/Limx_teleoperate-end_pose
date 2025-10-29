#!/usr/bin/env python3
"""独立测试图像客户端"""

import sys
import os
import time

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from image_service.image_client import ImageClient

def test_client():
    """测试图像客户端是否能连接并接收数据"""
    print("🚀 启动图像客户端测试...")
    print("配置：")
    print("  - 服务器: 10.192.1.3:5556")
    print("  - 显示窗口: 是")
    print("  - 不使用共享内存（独立测试）")
    print()
    
    # 创建图像客户端（启用统计和显示，不使用共享内存）
    client = ImageClient(
        img_shape=None,  # 不使用共享内存
        img_shm_name=None,  # 不使用共享内存
        image_show=True,  # 显示图像窗口
        server_address="10.192.1.3",
        port=5556,
        enable_stats=True  # 启用统计
    )
    
    # 启动客户端
    client.start()
    
    print("✅ 图像客户端已启动")
    print("等待接收图像数据...")
    print("按 Ctrl+C 停止")
    print()
    
    try:
        # 保持运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
    finally:
        client.close()
        print("✅ 测试完成")

if __name__ == '__main__':
    test_client()

