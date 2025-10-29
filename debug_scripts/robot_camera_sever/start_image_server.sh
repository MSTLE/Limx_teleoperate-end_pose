#!/bin/bash
# 启动 ROS2 RealSense 相机 + ZMQ 桥接程序
#  conda activate teleoperte
#  bash start_image_server.sh --stats

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
COMPRESSION_QUALITY=80
BASE_PORT=5555
ENABLE_STATS=false

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --compression)
            COMPRESSION_QUALITY="$2"
            shift 2
            ;;
        --port)
            BASE_PORT="$2"
            shift 2
            ;;
        --stats)
            ENABLE_STATS=true
            shift
            ;;
        --help)
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --compression N    JPEG 压缩质量 (0-100, 默认: 80)"
            echo "  --port N          起始 ZMQ 端口 (默认: 5555)"
            echo "  --stats           启用性能统计"
            echo "  --help            显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0 --compression 90 --port 5555 --stats"
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            echo "使用 --help 查看帮助"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}RealSense 相机启动脚本 (ROS2 + ZMQ 桥接)${NC}"
echo -e "${BLUE}====================================================${NC}"

# Source ROS2
if [ -f "/opt/ros/humble/setup.bash" ]; then
    source /opt/ros/humble/setup.bash
    echo -e "${GREEN}✅ ROS2 环境已加载${NC}"
else
    echo -e "${RED}❌ 错误: 找不到 ROS2 环境${NC}"
    exit 1
fi

# 检测相机
echo ""
echo -e "${YELLOW}🔍 检测 RealSense 相机...${NC}"
serial_numbers=($(rs-enumerate-devices | grep "Serial Number" | grep -v "Asic" | awk '{print $NF}'))

if [ ${#serial_numbers[@]} -eq 0 ]; then
    echo -e "${RED}❌ 错误: 未检测到 RealSense 相机${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 检测到 ${#serial_numbers[@]} 个相机:${NC}"
for i in "${!serial_numbers[@]}"; do
    echo "  相机 $i: ${serial_numbers[$i]}"
done

# 配置显示
echo ""
echo -e "${BLUE}配置:${NC}"
echo "  压缩质量: $COMPRESSION_QUALITY"
echo "  起始端口: $BASE_PORT"
echo "  性能统计: $ENABLE_STATS"
echo ""

# 存储进程 PID
PIDS=()

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}⚠️  正在停止所有进程...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait
    echo -e "${GREEN}✅ 所有进程已停止${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 启动每个相机
for i in "${!serial_numbers[@]}"; do
    serial=${serial_numbers[$i]}
    camera_name="camera$i"
    port=$((BASE_PORT + i))
    
    echo -e "${BLUE}====================================================${NC}"
    echo -e "${GREEN}🚀 启动相机 $i: $serial${NC}"
    echo -e "${BLUE}====================================================${NC}"
    
    # 启动 ROS2 相机节点
    echo "  1️⃣  启动 ROS2 相机节点 (topic: /$camera_name/*)..."
    ros2 launch realsense2_camera rs_launch.py \
        serial_no:="'$serial'" \
        camera_name:=$camera_name \
        enable_pointcloud:=false \
        enable_accel:=true \
        enable_gyro:=true \
        enable_sync:=true \
        unite_imu_method:=linear_interpolation \
        > /tmp/ros2_camera_${camera_name}.log 2>&1 &
    
    camera_pid=$!
    PIDS+=($camera_pid)
    echo "     PID: $camera_pid"
    
    # 等待相机启动
    echo "     等待相机初始化..."
    sleep 8
    
    # 启动 ZMQ 桥接
    echo "  2️⃣  启动 ZMQ 桥接 (端口: $port)..."
    
    # 构建统计参数
    stats_arg=""
    if [ "$ENABLE_STATS" = true ]; then
        stats_arg="--stats"
    fi
    
    # 使用 Python（优先使用当前环境）
    python /home/guest/xianpeng/teleoperate/ros2_to_zmq_bridge.py \
        --camera $camera_name \
        --port $port \
        --compression $COMPRESSION_QUALITY \
        $stats_arg \
        > /tmp/zmq_bridge_${camera_name}.log 2>&1 &
    
    bridge_pid=$!
    PIDS+=($bridge_pid)
    echo "     PID: $bridge_pid"
    
    echo -e "${GREEN}✅ 相机 $i 启动完成 (ZMQ 端口: $port)${NC}"
    echo ""
done

# 显示摘要
echo -e "${BLUE}====================================================${NC}"
echo -e "${GREEN}✅ 所有相机启动完成！${NC}"
echo -e "${BLUE}====================================================${NC}"
echo ""
echo "摘要:"
for i in "${!serial_numbers[@]}"; do
    port=$((BASE_PORT + i))
    echo "  相机 $i (${serial_numbers[$i]}):"
    echo "    - ROS2 topic: /camera$i/color/image_raw"
    echo "    - ZMQ 端口: $port"
done
echo ""
echo "日志文件:"
echo "  - ROS2 相机: /tmp/ros2_camera_*.log"
echo "  - ZMQ 桥接: /tmp/zmq_bridge_*.log"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 等待所有进程
wait

