#!/usr/bin/env python3
"""
计算正运动学：从关节角度计算末端位姿
"""

import json
import numpy as np

# 读取关节状态
with open('/home/wxp/project/LIMX/Limx_teleoperate-end_pose/debug_scripts/joint_state_mode1.json', 'r') as f:
    joint_state = json.load(f)

names = joint_state['names']
positions = joint_state['q']

# 找到双臂关节
print("="*60)
print("关节角度数据")
print("="*60)

left_arm_indices = {}
right_arm_indices = {}

for i, name in enumerate(names):
    if 'left_shoulder' in name or 'left_elbow' in name or 'left_wrist' in name:
        left_arm_indices[name] = i
    elif 'right_shoulder' in name or 'right_elbow' in name or 'right_wrist' in name:
        right_arm_indices[name] = i

print("\n左臂关节:")
for name, idx in sorted(left_arm_indices.items()):
    print(f"  {name:30s}: {positions[idx]:7.4f} rad ({positions[idx]*57.3:.1f}°)")

print("\n右臂关节:")
for name, idx in sorted(right_arm_indices.items()):
    print(f"  {name:30s}: {positions[idx]:7.4f} rad ({positions[idx]*57.3:.1f}°)")

# 尝试使用pinocchio计算FK
print("\n" + "="*60)
print("使用Pinocchio计算正运动学")
print("="*60)

try:
    import pinocchio as pin
    
    # 加载机器人模型
    urdf_path = "/home/wxp/project/LIMX/Limx_teleoperate-end_pose/xr_teleoperate/assets/HU_D04_description/urdf/HU_D04_01.urdf"
    
    print(f"\n加载URDF: {urdf_path}")
    
    # 只加载运动学模型，不加载mesh（避免路径问题）
    model = pin.buildModelFromUrdf(urdf_path)
    data = model.createData()
    
    # 或者使用RobotWrapper但忽略几何体
    # robot = pin.RobotWrapper.BuildFromURDF(urdf_path, package_dirs=["/home/wxp/project/LIMX/Limx_teleoperate-end_pose/xr_teleoperate/assets/HU_D04_description"], geometry_types=[])
    
    print(f"✅ 模型加载成功! 关节数: {model.nq}, 刚体数: {len(model.names)}")
    
    # 构造完整的关节配置向量
    q = np.array(positions)
    
    # 计算正运动学
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)
    
    # 查找左右手末端frame
    print("\n可用的frames:")
    for i, frame in enumerate(model.frames):
        if 'hand' in frame.name.lower() or 'wrist' in frame.name.lower():
            print(f"  {i}: {frame.name}")
    
    # 尝试找到左右手末端 - 优先使用hand_manip（操作点）
    left_hand_frames = ['left_hand_manip', 'left_hand_contact', 'left_wrist_roll_link', 'left_hand', 'left_end_effector']
    right_hand_frames = ['right_hand_manip', 'right_hand_contact', 'right_wrist_roll_link', 'right_hand', 'right_end_effector']
    
    left_frame_id = None
    right_frame_id = None
    
    for frame_name in left_hand_frames:
        if model.existFrame(frame_name):
            left_frame_id = model.getFrameId(frame_name)
            print(f"\n✅ 找到左手frame: {frame_name}")
            break
    
    for frame_name in right_hand_frames:
        if model.existFrame(frame_name):
            right_frame_id = model.getFrameId(frame_name)
            print(f"✅ 找到右手frame: {frame_name}")
            break
    
    if left_frame_id is not None:
        left_pose = data.oMf[left_frame_id]
        left_pos = left_pose.translation
        left_quat = pin.Quaternion(left_pose.rotation).coeffs()  # [x,y,z,w]
        
        print("\n" + "="*60)
        print("左手末端位姿 (相对于base_link)")
        print("="*60)
        print(f"位置 (xyz): [{left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f}]")
        print(f"四元数 (xyzw): [{left_quat[0]:.3f}, {left_quat[1]:.3f}, {left_quat[2]:.3f}, {left_quat[3]:.3f}]")
        print(f"四元数 (wxyz): [{left_quat[3]:.3f}, {left_quat[0]:.3f}, {left_quat[1]:.3f}, {left_quat[2]:.3f}]")
    
    if right_frame_id is not None:
        right_pose = data.oMf[right_frame_id]
        right_pos = right_pose.translation
        right_quat = pin.Quaternion(right_pose.rotation).coeffs()  # [x,y,z,w]
        
        print("\n" + "="*60)
        print("右手末端位姿 (相对于base_link)")
        print("="*60)
        print(f"位置 (xyz): [{right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f}]")
        print(f"四元数 (xyzw): [{right_quat[0]:.3f}, {right_quat[1]:.3f}, {right_quat[2]:.3f}, {right_quat[3]:.3f}]")
        print(f"四元数 (wxyz): [{right_quat[3]:.3f}, {right_quat[0]:.3f}, {right_quat[1]:.3f}, {right_quat[2]:.3f}]")
    
    # 比较
    print("\n" + "="*60)
    print("与当前step4设置的base_pos对比")
    print("="*60)
    
    current_left = [0.3, 0.2, 0.6]
    current_right = [0.3, -0.2, 0.6]
    
    if left_frame_id is not None:
        diff_left = np.array(left_pos) - np.array(current_left)
        print(f"\n左手:")
        print(f"  实际位置: [{left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f}]")
        print(f"  设定位置: {current_left}")
        print(f"  差值:     [{diff_left[0]:.3f}, {diff_left[1]:.3f}, {diff_left[2]:.3f}]")
        print(f"  差值距离: {np.linalg.norm(diff_left)*100:.1f} cm")
        
        if np.linalg.norm(diff_left) > 0.05:
            print(f"  ⚠️  差距 > 5cm! 第一次移动会很快!")
        else:
            print(f"  ✅ 差距 < 5cm, 安全")
    
    if right_frame_id is not None:
        diff_right = np.array(right_pos) - np.array(current_right)
        print(f"\n右手:")
        print(f"  实际位置: [{right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f}]")
        print(f"  设定位置: {current_right}")
        print(f"  差值:     [{diff_right[0]:.3f}, {diff_right[1]:.3f}, {diff_right[2]:.3f}]")
        print(f"  差值距离: {np.linalg.norm(diff_right)*100:.1f} cm")
        
        if np.linalg.norm(diff_right) > 0.05:
            print(f"  ⚠️  差距 > 5cm! 第一次移动会很快!")
        else:
            print(f"  ✅ 差距 < 5cm, 安全")
    
    # 建议
    print("\n" + "="*60)
    print("建议更新base_pos为:")
    print("="*60)
    if left_frame_id is not None and right_frame_id is not None:
        print(f"self.base_left_pos = [{left_pos[0]:.3f}, {left_pos[1]:.3f}, {left_pos[2]:.3f}]")
        print(f"self.base_right_pos = [{right_pos[0]:.3f}, {right_pos[1]:.3f}, {right_pos[2]:.3f}]")

except ImportError:
    print("\n❌ Pinocchio未安装")
    print("   安装: pip install pin")
except Exception as e:
    print(f"\n❌ 计算FK失败: {e}")
    import traceback
    traceback.print_exc()

