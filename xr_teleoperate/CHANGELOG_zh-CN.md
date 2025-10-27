# 🔖 版本说明

## 🏷️ v1.3

- 添加 [![Unitree LOGO](https://camo.githubusercontent.com/ff307b29fe96a9b115434a450bb921c2a17d4aa108460008a88c58a67d68df4e/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4769744875622d57696b692d3138313731373f6c6f676f3d676974687562)](https://github.com/unitreerobotics/xr_teleoperate/wiki) [![Unitree LOGO](https://camo.githubusercontent.com/6f5253a8776090a1f89fa7815e7543488a9ec200d153827b4bc7c3cb5e1c1555/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f2d446973636f72642d3538363546323f7374796c653d666c6174266c6f676f3d446973636f7264266c6f676f436f6c6f723d7768697465)](https://discord.gg/ZwcVwxv5rq)

- 支持 **IPC 模式**，默认使用 SSHKeyboard 进行输入控制。  
- 合并 **H1_2** 机器人新增运动模式支持。  
- 合并 **G1_23** 机械臂新增运动模式支持。  

------

- 优化了数据记录功能。  
- 改进了仿真环境中的夹持器（gripper）使用体验。  

------

- 通过在控制器启动前初始化 IK，修复了启动时的抖动问题。  
- 修复了 SSHKeyboard 停止监听的 bug。  
- 修复了启动按钮逻辑错误。  
- 修复了仿真模式中的若干 bug。  

## 🏷️ v1.2

1. 升级Dex1_1夹爪控制代码，匹配 [dex1_1 service](https://github.com/unitreerobotics/dex1_1_service) 驱动

## 🏷️ v1.1

1. 末端执行器类型新增'brainco'，这是[强脑科技第二代灵巧手](https://www.brainco-hz.com/docs/revolimb-hand/)
2. 为避免与实机部署时发生冲突，将仿真模式下的 dds 通道的domain id修改为1
3. 修复默认频率过高的问题

## 🏷️ v1.0 (newvuer)

1. 升级 [Vuer](https://github.com/vuer-ai/vuer) 库至 v0.0.60 版本，XR设备支持模式扩展为**手部跟踪**和**控制器跟踪**两种。为更准确反映功能范围，项目由 **avp_teleoperate** 更名为 **xr_teleoperate**。

   测试设备包括： Apple Vision Pro，Meta Quest 3（含手柄） 与 PICO 4 Ultra Enterprise（含手柄）。

2. 对部分功能进行了**模块化**拆分，并通过 Git 子模块（git submodule）方式进行管理和加载，提升代码结构的清晰度与维护性。

3. 新增**无头**、**运控**及**仿真**模式，优化启动参数配置（详见第2.2节），提升使用便捷性。**仿真**模式的加入，方便了环境验证和硬件故障排查。

4. 将默认手部映射算法从 Vector 切换为 **DexPilot**，优化了指尖捏合的精度与交互体验。

5. 其他一些优化

## 🏷️ v0.5 (oldvuer)

1. 该版本曾经命名为 `avp_teleoperate`
2. 支持 'G1_29', 'G1_23', 'H1_2', 'H1' 机器人类型
3. 支持 'dex3', 'gripper', 'inspire1' 末端执行器类型
4. 仅支持 XR 设备的手部跟踪模式（ [Vuer](https://github.com/vuer-ai/vuer) 版本为 v0.0.32RC7），不支持控制器模式
5. 支持数据录制模式