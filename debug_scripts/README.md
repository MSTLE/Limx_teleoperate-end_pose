# Limx机器人 Quest VR控制 - 调试脚本集

本文件夹包含从连接测试到VR控制的完整渐进式调试脚本。

## 📁 文件说明

### 核心脚本（按执行顺序）

1. **step1_test_connection.py** - WebSocket连接测试
   - 验证能否连接到机器人
   - 获取机器人SN

2. **step2_test_mode_switch.py** - 模式切换测试
   - 测试阻尼/准备/Mode 0/Mode 1/Mode 2模式切换
   - 验证基本控制指令

3. **step3_get_pose.py** - 位姿读取测试（可选）
   - 尝试读取末端位姿
   - 注意：实际API使用相对坐标，此步骤仅供参考

4. **step3b_get_joint_state.py** - 关节状态读取
   - 读取Mode 1时的关节角度
   - 保存到 `joint_state_mode1.json`

5. **compute_fk_from_joints.py** - 正运动学计算（可选）
   - 从关节角度计算末端位姿
   - 用于验证坐标系理解

6. **step4_safe_movement.py** - 安全移动测试 ⭐
   - 测试微小的平滑移动
   - 验证相对位姿控制
   - 包含零移动、渐进移动测试

7. **step5_keyboard_control.py** - 键盘实时控制
   - 用键盘控制机器人上肢
   - 验证实时控制循环（30Hz）
   - 为VR控制做准备

8. **step7_quest_real_control.py** - Quest VR实时控制 ⭐⭐⭐
   - 使用Meta Quest控制机器人（原版TeleVuerWrapper）
   - 支持手部追踪和手柄控制器
   - 包含标定、实时控制、安全退出
   - 使用真实Quest手柄/手部追踪
   - 完整的VR控制流程

### 辅助模块

- **televuer/** - VR通信模块（从xr_teleoperate复制）
  - `televuer.py` - 底层Vuer服务器封装
  - `tv_wrapper.py` - 高层接口，自动处理坐标转换
  - 完整的OpenXR支持（手部追踪+手柄控制器）
  
- **generate_ssl_cert.py** - SSL证书生成工具
  - 生成WebXR所需的自签名证书

### 数据文件

- **joint_state_mode1.json** - Mode 1时的关节状态
  - 由 `step3b` 生成
  - 用于FK计算

- **vr_calibration.pkl** - VR标定数据
  - 由 `step7` 首次标定时自动生成
  - 保存左右手参考位置矩阵
  - 下次运行可直接加载，无需重新标定

## 🚀 快速开始

### 1. 安装依赖

```bash
conda activate limx
pip install websocket-client numpy scipy pinocchio vuer pyOpenSSL
```

### 2. 生成SSL证书（VR控制必需）

WebXR需要HTTPS才能访问Quest的传感器。运行以下命令生成自签名证书：

```bash
python generate_ssl_cert.py
```

这会在当前目录生成 `cert.pem` 和 `key.pem` 两个文件。

**注意：**
- 自签名证书会在浏览器中显示安全警告
- 在Quest浏览器中点击"高级"→"继续访问"或"接受风险"即可

### 3. 连接测试

```bash
python step1_test_connection.py
```

### 4. 安全移动测试（推荐先测试）

```bash
python step4_safe_movement.py
```

### 5. 键盘控制测试

```bash
python step5_keyboard_control.py
```

### 6. Quest VR实时控制（最终版）

**使用原版TeleVuerWrapper**，最稳定可靠：

```bash
python step7_quest_real_control.py
```

**流程**:
1. 确认安全检查（机器人悬挂、SSL证书等）
2. 选择模式：**1** = 手柄控制器，**2** = 手部追踪
3. VR服务启动，在Quest浏览器访问 `https://vuer.ai?grid=False`
4. 等待Quest连接
5. 机器人初始化（阻尼→准备→Mode0→Mode1）
6. **标定**: 双手放在舒适位置，保持不动3秒
7. 开始实时控制！移动双手控制机器人

**标定说明**:
- 标定位置=控制的"零点"
- 所有移动都是相对标定位置的偏移
- 偏移自动限制在±20cm内保证安全
- **首次运行**会进行标定并保存到 `vr_calibration.pkl`
- **后续运行**可选择：
  - **1** = 使用保存的标定（推荐，节省时间）
  - **2** = 重新标定（如果换了操作位置）
- 删除 `vr_calibration.pkl` 可强制重新标定

## ⚠️ 安全注意事项

1. **必须悬挂机器人**！脚离地≥15cm
2. **遥控器随时在手边**，可按L2+X急停
3. **2米范围内无障碍物**
4. **至少2人在场**，1人操作VR，1人监控机器人
5. **从小移动开始测试**，逐步增加移动幅度

## 📊 坐标系说明

### API使用相对坐标系

```json
{
  "left_hand_pos": [0.0, 0.0, 0.0],  // 相对于Mode 0初始姿态的偏移
  "left_hand_quat": [0.0, 0.0, 0.0, 1.0]
}
```

- `[0, 0, 0]` = Mode 0姿态（肘部弯曲65度）
- `[0.01, 0, 0]` = 相对Mode 0，X方向前移1cm
- `[0, 0.01, 0]` = 相对Mode 0，Y方向左移1cm
- `[0, 0, 0.01]` = 相对Mode 0，Z方向上移1cm

### VR坐标系转换

**OpenXR坐标系:**
- X: 右
- Y: 上
- Z: 后

**机器人坐标系:**
- X: 前
- Y: 左
- Z: 上

转换由 `televuer/tv_wrapper.py` 中的 `TeleVuerWrapper` 自动处理。

## 🔧 工作空间限制

默认安全工作空间（相对于Mode 0）：
- X轴（前后）：-10cm ~ +20cm
- Y轴（左右）：±15cm
- Z轴（上下）：-15cm ~ +20cm

可在脚本中修改 `workspace` 参数调整。

## 📝 常见问题

### Q: 机器人移动太快？
A: 在step4中调整 `duration` 参数，增加移动时长。

### Q: VR连接不上？
A: 
1. **先生成SSL证书**：`python generate_ssl_cert.py`
2. 确保PC和Quest在同一WiFi
3. 检查防火墙是否允许8012端口（Vuer默认端口）
4. 在Quest浏览器中访问显示的HTTPS地址
5. 接受安全警告（自签名证书）
6. 授权WebXR权限（Quest会弹窗询问）

### Q: 零移动时机器人还是动了？
A: 这是正常的！`[0,0,0]` 对应Mode 0的理论位姿，实际关节可能有小误差。

### Q: 不想每次都标定？
A: **已支持自动保存标定！**
- 首次运行会标定并保存到 `vr_calibration.pkl`
- 后续运行选择 **1** 直接使用保存的标定
- 如果换了操作位置，选择 **2** 重新标定
- 删除标定文件：`rm vr_calibration.pkl`

### Q: 标定的是什么？
A: 标定你的"舒适姿势"作为控制零点：
- 标定时双手的位置 = 机器人Mode 1的初始位置
- 之后移动双手，机器人会跟随相对移动
- 好处：可以坐着/站着，不同高度都能控制

### Q: 如何调整移动灵敏度？
A: 在step7中添加缩放因子：
```python
self.robot_left_offset = (left_current - left_origin) * 0.5  # 50%灵敏度
```

## 🎯 项目结构

```
debug_scripts/
├── step1_test_connection.py      # 连接测试
├── step2_test_mode_switch.py     # 模式测试
├── step3_get_pose.py             # 位姿读取（可选）
├── step3b_get_joint_state.py     # 关节状态读取
├── compute_fk_from_joints.py     # FK计算（可选）
├── step4_safe_movement.py        # 安全移动测试 ⭐
├── step5_keyboard_control.py     # 键盘控制
├── step7_quest_real_control.py   # Quest VR实时控制 🎯
├── televuer/                     # VR通信模块（复制自xr_teleoperate）
│   ├── __init__.py
│   ├── televuer.py               # Vuer服务器封装
│   └── tv_wrapper.py             # 高层接口+坐标转换
├── generate_ssl_cert.py          # SSL证书生成工具
├── cert.pem                      # SSL证书（首次运行generate后生成）
├── key.pem                       # SSL密钥（首次运行generate后生成）
├── joint_state_mode1.json        # 关节数据（step3b生成）
├── vr_calibration.pkl            # VR标定数据（step7首次标定时生成）
└── README.md                     # 本文件
```

## 👥 贡献

本项目由AI助手协助开发，用于Limx机器人的VR遥操作研究。

