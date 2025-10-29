#!/usr/bin/env python3
"""
ROS2 到 ZeroMQ 桥接程序
从 ROS2 RealSense topics 读取图像，通过 ZeroMQ 发送
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import zmq
import time
import struct
import numpy as np
from collections import deque
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ROS2_ZMQ_Bridge')


class ImageBridge(Node):
    """ROS2 到 ZeroMQ 图像桥接"""
    
    def __init__(self, camera_name='camera0', port=5555, compression_quality=80, enable_stats=False):
        """初始化桥接器
        
        Args:
            camera_name: ROS2 相机名称（topic 前缀）
            port: ZeroMQ 端口
            compression_quality: JPEG 压缩质量 (0-100)
            enable_stats: 是否启用性能统计
        """
        super().__init__('image_bridge')
        
        self.camera_name = camera_name
        self.port = port
        self.compression_quality = compression_quality
        self.enable_stats = enable_stats
        
        # 初始化 CV Bridge
        self.bridge = CvBridge()
        
        # 订阅 ROS2 彩色图像 topic
        self.color_topic = f'/camera/{camera_name}/color/image_raw'
        self.color_sub = self.create_subscription(
            Image,
            self.color_topic,
            self.color_callback,
            10
        )
        
        logger.info(f"订阅 ROS2 topic: {self.color_topic}")
        
        # 初始化 ZeroMQ
        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PUB)
        self.zmq_socket.bind(f"tcp://*:{self.port}")
        logger.info(f"ZeroMQ 服务器启动，绑定端口: {self.port}")
        
        # 性能统计
        if self.enable_stats:
            self._init_stats()
        
        logger.info(f"✅ 桥接器初始化完成 ({camera_name} -> ZMQ:{port})")
    
    def _init_stats(self):
        """初始化性能统计"""
        self.frame_count = 0
        self.time_window = 1.0  # 1秒统计窗口
        self.frame_times = deque()
        self.start_time = time.time()
    
    def _update_stats(self, current_time):
        """更新性能统计"""
        self.frame_times.append(current_time)
        # 移除超出窗口的时间戳
        while self.frame_times and self.frame_times[0] < current_time - self.time_window:
            self.frame_times.popleft()
        self.frame_count += 1
    
    def _print_stats(self, current_time):
        """打印性能统计"""
        if self.frame_count % 30 == 0:
            elapsed_time = current_time - self.start_time
            real_fps = len(self.frame_times) / self.time_window if self.frame_times else 0
            logger.info(f"📊 [{self.camera_name}] FPS: {real_fps:.1f}, 总帧数: {self.frame_count}, 运行时间: {elapsed_time:.1f}s")
    
    def color_callback(self, msg):
        """处理彩色图像回调"""
        try:
            # 转换 ROS Image 到 OpenCV 格式
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            
            # JPEG 压缩
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.compression_quality]
            ret, buffer = cv2.imencode('.jpg', cv_image, encode_param)
            if not ret:
                logger.error("图像编码失败")
                return
            
            jpg_bytes = buffer.tobytes()
            
            # 添加时间戳（用于延迟测量）
            if self.enable_stats:
                timestamp = time.time()
                frame_id = self.frame_count
                header = struct.pack('dI', timestamp, frame_id)  # 8字节时间戳 + 4字节帧ID
                message = header + jpg_bytes
            else:
                message = jpg_bytes
            
            # 发送图像
            self.zmq_socket.send(message)
            
            # 更新统计
            if self.enable_stats:
                current_time = time.time()
                self._update_stats(current_time)
                self._print_stats(current_time)
        
        except Exception as e:
            logger.error(f"处理图像失败: {e}")
    
    def destroy_node(self):
        """清理资源"""
        logger.info("正在关闭桥接器...")
        self.zmq_socket.close()
        self.zmq_context.term()
        super().destroy_node()
        logger.info("✅ 桥接器已关闭")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ROS2 到 ZeroMQ 图像桥接器')
    parser.add_argument('--camera', type=str, default='camera0',
                        help='ROS2 相机名称（topic 前缀）')
    parser.add_argument('--port', type=int, default=5555, help='ZeroMQ 端口')
    parser.add_argument('--compression', type=int, default=80, help='JPEG 压缩质量 (0-100)')
    parser.add_argument('--stats', action='store_true', help='启用性能统计')
    
    args = parser.parse_args()
    
    # 初始化 ROS2
    rclpy.init()
    
    # 创建桥接器
    bridge = ImageBridge(
        camera_name=args.camera,
        port=args.port,
        compression_quality=args.compression,
        enable_stats=args.stats
    )
    
    try:
        logger.info("🚀 桥接器开始运行，等待 ROS2 图像数据...")
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        logger.warning("⚠️  用户中断")
    except Exception as e:
        logger.error(f"❌ 桥接器运行错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bridge.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

