#!/usr/bin/env python3
# 版权信息
#
# © [2025] LimX Dynamics Technology Co., Ltd. 保留所有权利。

"""
图像客户端（运行在主机端）

功能：
- 从机器人端接收图像数据
- 通过共享内存传递给 TeleVuer/XR 显示
- 性能监控（延迟、丢帧等）
"""

import cv2
import zmq
import numpy as np
import time
import struct
from collections import deque
from multiprocessing import shared_memory
from typing import Optional, Tuple
import logging
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ImageClient')


class ImageClient:
    """图像客户端
    
    从图像服务器接收图像并通过共享内存传递
    """
    
    def __init__(
        self,
        img_shape: Optional[Tuple[int, int, int]] = None,
        img_shm_name: Optional[str] = None,
        image_show: bool = False,
        server_address: str = "10.192.1.2",
        port: int = 5556,
        enable_stats: bool = False
    ):
        """初始化图像客户端
        
        Args:
            img_shape: 图像形状 (height, width, channels)
            img_shm_name: 共享内存名称（用于传递给 TeleVuer）
            image_show: 是否显示图像窗口（调试用）
            server_address: 服务器IP地址（机器人端）
            port: ZeroMQ 端口
            enable_stats: 是否启用性能统计
        """
        self.running = True
        self.img_shape = img_shape
        self.img_shm_name = img_shm_name
        self.image_show = image_show
        self.server_address = server_address
        self.port = port
        self.enable_stats = enable_stats
        
        # 共享内存（延迟连接，在run()中初始化）
        self.enable_shm = False
        self.image_shm = None
        self.img_array = None
        
        # 性能统计
        if self.enable_stats:
            self._init_stats()
        
        # ZeroMQ
        self.context = None
        self.socket = None
    
    def _init_stats(self):
        """初始化性能统计"""
        self.frame_count = 0
        self.last_frame_id = -1
        
        # 实时 FPS
        self.time_window = 1.0  # 1秒窗口
        self.frame_times = deque()
        
        # 延迟统计
        self.latencies = deque()
        self.lost_frames = 0
        self.total_frames = 0
    
    def _update_stats(self, timestamp: float, frame_id: int, receive_time: float):
        """更新性能统计"""
        # 延迟
        latency = receive_time - timestamp
        self.latencies.append(latency)
        
        # 移除超出窗口的延迟
        while self.latencies and self.frame_times and self.latencies[0] < receive_time - self.time_window:
            self.latencies.popleft()
        
        # 帧时间
        self.frame_times.append(receive_time)
        while self.frame_times and self.frame_times[0] < receive_time - self.time_window:
            self.frame_times.popleft()
        
        # 丢帧检测
        expected_frame_id = self.last_frame_id + 1 if self.last_frame_id != -1 else frame_id
        if frame_id != expected_frame_id:
            lost = frame_id - expected_frame_id
            if lost > 0:
                self.lost_frames += lost
                logger.warning(f"⚠️  检测到丢帧: {lost}, 期望帧ID: {expected_frame_id}, 实际帧ID: {frame_id}")
        
        self.last_frame_id = frame_id
        self.total_frames = frame_id + 1
        self.frame_count += 1
    
    def _print_stats(self, receive_time: float):
        """打印性能统计"""
        if self.frame_count % 30 == 0:
            # FPS
            real_fps = len(self.frame_times) / self.time_window if self.frame_times else 0
            
            # 延迟统计
            if self.latencies:
                avg_latency = sum(self.latencies) / len(self.latencies) * 1000  # ms
                max_latency = max(self.latencies) * 1000
                min_latency = min(self.latencies) * 1000
                jitter = max_latency - min_latency
            else:
                avg_latency = max_latency = min_latency = jitter = 0
            
            # 丢帧率
            lost_rate = (self.lost_frames / self.total_frames) * 100 if self.total_frames > 0 else 0
            
            logger.info(
                f"📊 FPS: {real_fps:.1f} | "
                f"延迟: {avg_latency:.1f}ms (min={min_latency:.1f}, max={max_latency:.1f}) | "
                f"抖动: {jitter:.1f}ms | "
                f"丢帧率: {lost_rate:.2f}%"
            )
    
    def start(self):
        """启动图像客户端（在单独线程中运行）"""
        self.receive_thread = threading.Thread(target=self.run, daemon=True)
        self.receive_thread.start()
        logger.info("✅ 图像客户端已在后台启动")
    
    def run(self):
        """运行图像客户端主循环"""
        # 延迟连接共享内存（确保 XR 接口已创建）
        if self.img_shape is not None and self.img_shm_name is not None:
            # 重试机制：最多尝试5次，每次间隔0.5秒
            for attempt in range(5):
                try:
                    time.sleep(0.5)  # 给 XR 接口时间创建共享内存
                    self.image_shm = shared_memory.SharedMemory(name=self.img_shm_name)
                    self.img_array = np.ndarray(self.img_shape, dtype=np.uint8, buffer=self.image_shm.buf)
                    self.enable_shm = True
                    logger.info(f"✅ 共享内存已连接: {self.img_shm_name}, 形状: {self.img_shape}")
                    break
                except FileNotFoundError:
                    if attempt < 4:
                        logger.warning(f"⚠️  共享内存未就绪，重试 {attempt+1}/5...")
                    else:
                        logger.error(f"❌ 共享内存连接失败: {self.img_shm_name}")
                        logger.info("提示: 请确保 XR 接口已正确初始化")
        
        # 初始化 ZeroMQ
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{self.server_address}:{self.port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        
        logger.info(f"🚀 图像客户端运行中，连接到: {self.server_address}:{self.port}")
        
        # 等待一小段时间让 ZeroMQ 订阅完全建立
        time.sleep(0.1)
        
        # 跳过启动时的前几帧（可能不完整）
        skipped_frames = 0
        max_skip = 5
        
        try:
            while self.running:
                # 接收消息
                message = self.socket.recv()
                receive_time = time.time()
                
                # 解析消息（始终跳过12字节头部: 8字节timestamp + 4字节frame_id）
                header_size = struct.calcsize('dI')  # 8+4=12字节
                if len(message) < header_size:
                    logger.warning(f"消息太短: {len(message)} 字节，期望至少 {header_size} 字节")
                    continue
                
                try:
                    header = message[:header_size]
                    jpg_bytes = message[header_size:]
                    
                    # 只有在启用统计时才解析和使用头部数据
                    if self.enable_stats:
                        timestamp, frame_id = struct.unpack('dI', header)
                except struct.error as e:
                    logger.warning(f"解析消息头失败: {e}, 消息长度: {len(message)}")
                    continue
                
                # 解码图像
                np_img = np.frombuffer(jpg_bytes, dtype=np.uint8)
                current_image = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                
                if current_image is None:
                    # 启动时跳过前几个可能损坏的帧
                    if skipped_frames < max_skip:
                        skipped_frames += 1
                        if skipped_frames == 1:
                            logger.info(f"跳过启动时的损坏帧（这是正常的）...")
                        continue
                    logger.warning(f"图像解码失败 - JPEG 数据长度: {len(jpg_bytes)}, 前16字节: {jpg_bytes[:16].hex() if len(jpg_bytes) >= 16 else jpg_bytes.hex()}")
                    continue
                
                # 第一次成功解码时记录
                if skipped_frames > 0 and skipped_frames <= max_skip:
                    logger.info(f"✅ 图像接收正常！形状: {current_image.shape}")
                    skipped_frames = max_skip + 10  # 避免重复记录
                
                # 写入共享内存
                if self.enable_shm:
                    # 调整尺寸（如果需要）
                    if current_image.shape != self.img_shape:
                        current_image = cv2.resize(current_image, (self.img_shape[1], self.img_shape[0]))
                    np.copyto(self.img_array, current_image)
                
                # 显示图像（调试用）
                if self.image_show:
                    height, width = current_image.shape[:2]
                    # 缩小一半显示
                    resized_image = cv2.resize(current_image, (width // 2, height // 2))
                    cv2.imshow('Image Client', resized_image)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.running = False
                        break
                
                # 更新统计
                if self.enable_stats:
                    self._update_stats(timestamp, frame_id, receive_time)
                    self._print_stats(receive_time)
        
        except KeyboardInterrupt:
            logger.warning("⚠️  用户中断")
        except Exception as e:
            logger.error(f"❌ 客户端运行错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()
    
    def close(self):
        """关闭客户端"""
        logger.info("正在关闭图像客户端...")
        
        self.running = False
        
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        
        if self.image_show:
            cv2.destroyAllWindows()
        
        logger.info("✅ 图像客户端已关闭")


def main():
    """主函数（用于测试）"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LimX 图像客户端')
    parser.add_argument('--server', type=str, default='10.192.1.2', help='服务器IP地址')
    parser.add_argument('--port', type=int, default=5555, help='ZeroMQ 端口')
    parser.add_argument('--show', action='store_true', help='显示图像窗口')
    parser.add_argument('--stats', action='store_true', help='启用性能统计')
    
    args = parser.parse_args()
    
    # 启动客户端
    client = ImageClient(
        image_show=args.show,
        server_address=args.server,
        port=args.port,
        enable_stats=args.stats
    )
    
    client.run()


if __name__ == "__main__":
    main()
