# Limx机器人 Quest VR遥操作系统

基于Meta Quest的人形机器人VR遥操作系统，支持双臂位姿控制、夹爪控制、头部姿态控制和实时视觉反馈。

## ✨ 核心特性

- 🎮 **VR遥操作**: 使用Meta Quest手部追踪或手柄控制机器人双臂
- 🤏 **Pinch夹爪控制**: 通过捏合手势或Grip按钮控制夹爪开合
- 🎯 **平滑运动**: 指数平滑滤波，让机器人动作更自然
- 👁️ **头部跟随**: VR头显俯仰角实时控制机器人头部姿态（-30° ~ 45°）
- 📹 **视觉反馈**: 机器人摄像头画面实时传输到VR头显
- 🔒 **安全保护**: 工作空间限制、速度限制、标定机制

## 📁 项目结构

### 核心文件

- **quest_real_control.py** - VR遥操作主程序 ⭐
  - 完整的VR控制流程
  - 支持手部追踪和手柄控制器
  - Pinch手势控制夹爪
  - 头部姿态跟随
  - 平滑运动控制
  - 标定与工作空间限制

### 辅助模块

- **televuer/** - VR通信模块
  - `televuer.py` - Vuer服务器封装
  - `tv_wrapper.py` - 高层接口，处理OpenXR坐标转换
  
- **image_service/** - 图像传输客户端
  - `image_client.py` - 从机器人接收图像并传递给VR显示
  - `ros2_to_zmq_bridge.py` - ROS2到ZMQ桥接（已弃用，见robot_camera_sever）

- **robot_camera_sever/** - 机器人端图像服务
  - `ros2_to_zmq_bridge.py` - ROS2相机数据到ZMQ桥接
  - `start_image_server.sh` - 启动脚本（在机器人端运行）

- **generate_ssl_cert.py** - SSL证书生成工具
  - 生成WebXR所需的自签名证书

### 数据文件

- **vr_calibration.pkl** - VR标定数据
  - 首次运行时自动生成
  - 保存左右手参考位置矩阵
  - 后续运行可直接加载

- **joint_state_mode1.json** - 关节状态参考数据
  - Mode 1时的关节角度记录

## 🚀 快速开始

### 1. 环境准备

**主机端（控制端）：**
```bash
conda activate limx
pip install websocket-client numpy scipy vuer pyOpenSSL zmq opencv-python
```

**机器人端（需要ROS2环境）：**
```bash
conda activate teleoperte  # 或你的ROS2环境
# 确保已安装: rclpy, cv_bridge, sensor_msgs, zmq
```

### 2. 生成SSL证书

WebXR需要HTTPS才能访问Quest传感器：

```bash
python generate_ssl_cert.py
```

生成 `cert.pem` 和 `key.pem`。Quest浏览器会显示安全警告，点击"高级"→"继续访问"即可。

### 3. 启动图像服务（可选）

如果需要在VR中看到机器人视角，在**机器人端**运行：

```bash
cd robot_camera_sever
bash start_image_server.sh --stats
```

参数说明：
- `--compression N`: JPEG压缩质量（0-100，默认80）
- `--port N`: ZMQ端口（默认5555）
- `--stats`: 启用性能统计

### 4. 运行VR遥操作

在**主机端**运行：

```bash
python quest_real_control.py
```

**操作流程：**

1. **安全确认**
   - 确保机器人悬挂（脚离地≥15cm）
   - 遥控器在手边（L2+X急停）
   - 2米范围内无障碍物

2. **参数设置**
   - 选择控制模式：1=手柄控制器，2=手部追踪
   - 设置运动缩放系数（推荐1.5-2.0）
   - 选择是否启用图像传输

3. **VR连接**
   - Quest浏览器访问 `https://vuer.ai?grid=False`
   - 授权WebXR权限
   - 等待连接成功

4. **机器人初始化**
   - 自动切换：阻尼→准备→Mode0→Mode1

5. **标定**
   - 首次运行：双手放舒适位置，保持不动3秒
   - 后续运行：选择加载已保存标定或重新标定

6. **开始控制**
   - 移动双手控制机器人手臂
   - Pinch手势（捏合）或Grip按钮控制夹爪
   - VR头显俯仰控制机器人头部

## ⚠️ 安全注意事项

1. **必须悬挂机器人**！脚离地≥15cm
2. **遥控器随时在手边**，可按L2+X急停
3. **2米范围内无障碍物**
4. **至少2人在场**，1人操作VR，1人监控机器人
5. **从小移动开始测试**，逐步增加移动幅度

## 📊 坐标系说明

### Base_link坐标系（机器人腰部）

本系统使用机器人腰部（base_link）作为参考坐标系：

- **X轴（红色）**: 机器人前进方向
- **Y轴（绿色）**: 正方向向左
- **Z轴（蓝色）**: 竖直向上

### VR坐标系转换

**OpenXR坐标系：**
- X: 右
- Y: 上  
- Z: 后

**转换处理：** `televuer/tv_wrapper.py` 中的 `TeleVuerWrapper` 自动处理坐标转换

### 工作空间限制

默认安全工作空间（baselink坐标系下的绝对范围）：

```python
workspace = {
    'x_min': -0.50, 'x_max': 0.80,   # 前后范围（米）
    'y_min': -0.80, 'y_max': 0.80,   # 左右范围（米）
    'z_min': 0.20, 'z_max': 1.50     # 高度范围（腰部以上）
}
```

可在 `quest_real_control.py` 中修改 `RobotController` 类的 `workspace` 参数。

## 🎮 控制说明

### 手臂控制
- 移动VR手部或手柄，机器人手臂实时跟随
- 运动缩放系数可调（默认1.5倍）
- 平滑滤波让动作更自然

### 夹爪控制

**Pinch手势控制（手部追踪模式）：**
- Pinch值范围：0.0（捏紧）~ 0.1+（分开）
- 夹爪映射：
  - `pinch ≤ 0.0` → 夹爪完全闭合（0）
  - `pinch ≥ 0.1` → 夹爪完全张开（1000）
  - 中间值线性插值

**Grip按钮控制（手柄模式）：**
- 按下Grip按钮 → 夹爪闭合
- 松开Grip按钮 → 夹爪张开

### 头部控制
- VR头显俯仰角实时控制机器人头部
- 范围：-30° ~ 45°

## ⚙️ 参数调整

在 `quest_real_control.py` 的 `RobotController` 类中可调整：

```python
# 平滑控制
enable_smoothing = True          # 是否启用平滑
smoothing_factor = 0.3           # 平滑系数 0.0-1.0（越小越快，越大越平滑）

# 速度限制
enable_velocity_limit = False    # 是否限速
max_velocity = 0.15              # 最大速度 m/s

# 运动缩放
motion_scale = 1.5               # 运动缩放系数（1.0-3.0）

# 夹爪参数
gripper_speed = 500              # 夹爪速度 [0, 1000]
gripper_force = 300              # 夹爪力度 [0, 1000]

# Pinch阈值（第577行附近）
PINCH_MAX = 0.10                 # Pinch最大值
```

## 📝 常见问题

### Q: VR连接不上？
**A:** 检查以下步骤：
1. 生成SSL证书：`python generate_ssl_cert.py`
2. 确保PC和Quest在同一WiFi
3. 检查防火墙是否允许8012端口
4. Quest浏览器访问 `https://vuer.ai?grid=False`
5. 接受安全警告并授权WebXR权限

### Q: 标定是什么？
**A:** 标定你的"舒适姿势"作为控制零点：
- 标定时双手位置 = 机器人当前位置
- 之后移动双手，机器人跟随相对移动
- 可以坐着/站着，不同高度都能控制
- 首次运行标定并保存到 `vr_calibration.pkl`
- 后续运行可选择加载或重新标定

### Q: 如何调整灵敏度？
**A:** 修改 `motion_scale` 参数：
- 增大 = 机器人移动范围更大
- 减小 = 机器人移动范围更小
- 推荐范围：1.5-2.0

### Q: 机器人动作太抖？
**A:** 调整平滑参数：
- 增大 `smoothing_factor`（如0.5）= 更平滑但延迟更大
- 减小 `smoothing_factor`（如0.2）= 响应更快但更抖
- 或启用速度限制：`enable_velocity_limit = True`

### Q: 夹爪没有响应？
**A:** 检查以下几点：
1. 确保机器人已初始化到Mode 1
2. 确认使用因时二指夹爪
3. 手部追踪模式：Quest能正确识别Pinch手势
4. 手柄模式：尝试按下Grip按钮
5. 查看控制台夹爪开口度数值是否变化

### Q: 图像传输延迟高？
**A:** 调整压缩质量：
```bash
bash start_image_server.sh --compression 60  # 降低质量提高速度
```

## 🎯 技术架构

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│ Meta Quest  │ WebXR   │   主机端     │ WebSocket│  机器人端   │
│  (VR头显)   │◄───────►│quest_real_   │◄────────►│  Limx API   │
│             │  HTTPS  │control.py    │   5000   │             │
└─────────────┘         └──────────────┘         └─────────────┘
                              │                         │
                              │ ZMQ                     │ ROS2
                              │ 5555/5556               │
                              ▼                         ▼
                        ┌──────────────┐         ┌─────────────┐
                        │ image_client │         │ RealSense   │
                        │    (接收)     │         │  相机节点    │
                        └──────────────┘         └─────────────┘
```

## 📂 完整目录结构

```
Limx_teleoperate-end_pose/
├── quest_real_control.py         # VR遥操作主程序 ⭐
├── generate_ssl_cert.py          # SSL证书生成工具
├── cert.pem                      # SSL证书
├── key.pem                       # SSL密钥
├── vr_calibration.pkl            # VR标定数据（自动生成）
├── joint_state_mode1.json        # 关节状态参考
├── televuer/                     # VR通信模块
│   ├── __init__.py
│   ├── televuer.py               # Vuer服务器封装
│   └── tv_wrapper.py             # OpenXR坐标转换
├── image_service/                # 图像传输客户端
│   ├── __init__.py
│   └── image_client.py           # 接收机器人图像
├── robot_camera_sever/           # 机器人端图像服务
│   ├── ros2_to_zmq_bridge.py    # ROS2到ZMQ桥接
│   └── start_image_server.sh    # 启动脚本
└── README.md                     # 本文件
```

