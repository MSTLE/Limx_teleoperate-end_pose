# 🔖 Release Note

## 🏷️ v1.3

- add [![Unitree LOGO](https://camo.githubusercontent.com/ff307b29fe96a9b115434a450bb921c2a17d4aa108460008a88c58a67d68df4e/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4769744875622d57696b692d3138313731373f6c6f676f3d676974687562)](https://github.com/unitreerobotics/xr_teleoperate/wiki) [![Unitree LOGO](https://camo.githubusercontent.com/6f5253a8776090a1f89fa7815e7543488a9ec200d153827b4bc7c3cb5e1c1555/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f2d446973636f72642d3538363546323f7374796c653d666c6174266c6f676f3d446973636f7264266c6f676f436f6c6f723d7768697465)](https://discord.gg/ZwcVwxv5rq)

- Support **IPC mode**, defaulting to use SSHKeyboard for input control.
- Merged motion mode support for H1_2 robot.
- Merged motion mode support for the G1_23 robot arm.

------

- Optimized data recording functionality.
- Improved gripper usage in simulation environment.

------

- Fixed startup oscillation by initializing IK before controller activation.
- Fixed SSHKeyboard stop-listening bug.
- Fixed logic of the start button.
- Fixed various bugs in simulation mode.

## 🏷️ v1.2

1. Upgrade the Dex1_1 gripper control code to be compatible with the [dex1_1 service](https://github.com/unitreerobotics/dex1_1_service) driver.

## 🏷️ v1.1

1. Added support for a new end-effector type: **`brainco`**, which refers to the [Brain Hand](https://www.brainco-hz.com/docs/revolimb-hand/) developed by [BrainCo](https://www.brainco.cn/#/product/dexterous).
2. Changed the **DDS domain ID** to `1` in **simulation mode** to prevent conflicts during physical deployment.
3. Fixed an issue where the default frequency was set too high.

## 🏷️ v1.0 (newvuer)

1. Upgraded the [Vuer](https://github.com/vuer-ai/vuer) library to version **v0.0.60**, expanding XR device support to two modes: **hand tracking** and **controller tracking**. The project has been renamed from **`avp_teleoperate`** to **`xr_teleoperate`** to better reflect its broader capabilities.

   Devices tested include: Apple Vision Pro, Meta Quest 3 (with controllers), and PICO 4 Ultra Enterprise (with controllers).

2. Modularized parts of the codebase and integrated **Git submodules** (`git submodule`) to improve code clarity and maintainability.

3. Introduced **headless**, **motion control**, and **simulation** modes. Startup parameter configuration has been streamlined for ease of use (see Section 2.2).
   The **simulation** mode enables environment validation and hardware failure diagnostics.

4. Changed the default hand retargeting algorithm from *Vector* to **DexPilot**, enhancing the precision and intuitiveness of fingertip pinching interactions.

5. Various other improvements and optimizations.

## 🏷️ v0.5 (oldvuer)

1. The repository was named **`avp_teleoperate`** in this version.
2. Supported robot included: `G1_29`, `G1_23`, `H1_2`, and `H1`.
3. Supported end-effectors included: `dex3`, `dex1(gripper)`, and `inspire1`.
4. Only supported **hand tracking mode** for XR devices (using [Vuer](https://github.com/vuer-ai/vuer) version **v0.0.32RC7**).
   **Controller tracking mode** was **not** supported. 
5. Data recording mode was available.