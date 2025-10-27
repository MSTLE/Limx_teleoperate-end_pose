<div align="center">
  <h1 align="center">xr_teleoperate</h1>
  <a href="https://www.unitree.com/" target="_blank">
    <img src="https://www.unitree.com/images/0079f8938336436e955ea3a98c4e1e59.svg" alt="Unitree LOGO" width="15%">
  </a>
  <p align="center">
    <a> English </a> | <a href="README_zh-CN.md">中文</a> | <a href="README_ja-JP.md">日本語</a>
  </p>
  <p align="center">
    <a href="https://github.com/unitreerobotics/xr_teleoperate/wiki" target="_blank"> <img src="https://img.shields.io/badge/GitHub-Wiki-181717?logo=github" alt="Unitree LOGO"></a> <a href="https://discord.gg/ZwcVwxv5rq" target="_blank"><img src="https://img.shields.io/badge/-Discord-5865F2?style=flat&logo=Discord&logoColor=white" alt="Unitree LOGO"></a>
  </p>
</div>


# 📺 Video Demo

<p align="center">
  <table>
    <tr>
      <td align="center" width="50%">
        <a href="https://www.youtube.com/watch?v=OTWHXTu09wE" target="_blank">
          <img src="https://img.youtube.com/vi/OTWHXTu09wE/maxresdefault.jpg" alt="Video 1" width="75%">
        </a>
        <p><b> G1 (29DoF) + Dex3-1 </b></p>
      </td>
      <td align="center" width="50%">
        <a href="https://www.youtube.com/watch?v=pNjr2f_XHoo" target="_blank">
          <img src="https://img.youtube.com/vi/pNjr2f_XHoo/maxresdefault.jpg" alt="Video 2" width="75%">
        </a>
        <p><b> H1_2 (Arm 7DoF) </b></p>
      </td>
    </tr>
  </table>
</p>


# 🔖[Release Note](CHANGELOG.md)

## 🏷️ v1.3

- add [![Unitree LOGO](https://camo.githubusercontent.com/ff307b29fe96a9b115434a450bb921c2a17d4aa108460008a88c58a67d68df4e/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f4769744875622d57696b692d3138313731373f6c6f676f3d676974687562)](https://github.com/unitreerobotics/xr_teleoperate/wiki) [![Unitree LOGO](https://camo.githubusercontent.com/6f5253a8776090a1f89fa7815e7543488a9ec200d153827b4bc7c3cb5e1c1555/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f2d446973636f72642d3538363546323f7374796c653d666c6174266c6f676f3d446973636f7264266c6f676f436f6c6f723d7768697465)](https://discord.gg/ZwcVwxv5rq)

- Support **IPC mode**, defaulting to use SSHKeyboard for input control.
- Merged motion mode support for H1_2 robot.
- Merged motion mode support for the G1_23 robot arm.

- ···

# 0. 📖 Introduction

This repository implements **teleoperation** control of a **Unitree humanoid robot** using **XR (Extended Reality) devices** (such as Apple Vision Pro, PICO 4 Ultra Enterprise, or Meta Quest 3). 

> If you have never worked with a Unitree robot before, please at least read up to the “Application Development” chapter in the [official documentation](https://support.unitree.com/main/en) first.
Additionally, the [Wiki of this repo](https://github.com/unitreerobotics/xr_teleoperate/wiki) contains a wealth of background knowledge that you can reference at any time.

Here are the required devices and wiring diagram,

<p align="center">
  <a href="https://oss-global-cdn.unitree.com/static/3f75e91e41694ed28c29bcad22954d1d_5990x4050.png">
    <img src="https://oss-global-cdn.unitree.com/static/3f75e91e41694ed28c29bcad22954d1d_5990x4050.png" alt="System Diagram" style="width: 100%;">
  </a>
</p>


The currently supported devices in this repository:

<table>
  <tr>
    <th align="center">🤖 Robot</th>
    <th align="center">⚪ Status</th>
  </tr>
  <tr>
    <td align="center"><a href="https://www.unitree.com/cn/g1" target="_blank">G1 (29 DoF)</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td align="center"><a href="https://www.unitree.com/cn/g1" target="_blank">G1 (23 DoF)</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td align="center"><a href="https://www.unitree.com/cn/h1" target="_blank">H1 (4‑DoF arm)</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td align="center"><a href="https://www.unitree.com/cn/h1" target="_blank">H1_2 (7‑DoF arm)</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td align="center"><a href="https://www.unitree.com/cn/Dex1-1" target="_blank">Dex1‑1 gripper</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td align="center"><a href="https://www.unitree.com/cn/Dex3-1" target="_blank">Dex3‑1 dexterous hand</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td align="center"><a href="https://support.unitree.com/home/zh/G1_developer/inspire_dfx_dexterous_hand" target="_blank">Inspire dexterous hand</a></td>
    <td align="center">✅ Complete</td>
  </tr>
  <tr>
    <td style="text-align: center;"> <a href="https://www.brainco-hz.com/docs/revolimb-hand/" target="_blank"> BrainCo dexterous hand </td>
    <td style="text-align: center;"> &#9989; Complete </td>
  </tr>
  <tr>
    <td align="center"> ··· </td>
    <td align="center"> ··· </td>
  </tr>
</table>



# 1. 📦 Installation

We tested our code on Ubuntu 20.04 and Ubuntu 22.04, other operating systems may be configured differently. This document primarily describes the **default mode**.

For more information, you can refer to [Official Documentation ](https://support.unitree.com/home/zh/Teleoperation) and [OpenTeleVision](https://github.com/OpenTeleVision/TeleVision).

## 1.1 📥 basic

```bash
# Create a conda environment
(base) unitree@Host:~$ conda create -n tv python=3.10 pinocchio=3.1.0 numpy=1.26.4 -c conda-forge
(base) unitree@Host:~$ conda activate tv
# Clone this repo
(tv) unitree@Host:~$ git clone https://github.com/unitreerobotics/xr_teleoperate.git
(tv) unitree@Host:~$ cd xr_teleoperate
# Shallow clone submodule
(tv) unitree@Host:~/xr_teleoperate$ git submodule update --init --depth 1
# Install televuer submodule
(tv) unitree@Host:~/xr_teleoperate$ cd teleop/televuer
(tv) unitree@Host:~/xr_teleoperate/teleop/televuer$ pip install -e .
# Generate the certificate files required for televuer submodule
(tv) unitree@Host:~/xr_teleoperate/teleop/televuer$ openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem
# Install dex-retargeting submodule
(tv) unitree@Host:~/xr_teleoperate/teleop/televuer$ cd ../robot_control/dex-retargeting/
(tv) unitree@Host:~/xr_teleoperate/teleop/robot_control/dex-retargeting$ pip install -e .
# Install additional dependencies required by this repo
(tv) unitree@Host:~/xr_teleoperate/teleop/robot_control/dex-retargeting$ cd ../../../
(tv) unitree@Host:~/xr_teleoperate$ pip install -r requirements.txt
```

## 1.2 🕹️ unitree_sdk2_python

```bash
# Install unitree_sdk2_python library which handles communication with the robot
(tv) unitree@Host:~$ git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
(tv) unitree@Host:~$ cd unitree_sdk2_python
(tv) unitree@Host:~/unitree_sdk2_python$ pip install -e .
```

> **Note 1:** For `xr_teleoperate` versions **v1.1 and above**, please ensure that the `unitree_sdk2_python` repository is checked out to a commit **equal to or newer than** [404fe44d76f705c002c97e773276f2a8fefb57e4](https://github.com/unitreerobotics/unitree_sdk2_python/commit/404fe44d76f705c002c97e773276f2a8fefb57e4).
>
> **Note 2**: The [unitree_dds_wrapper](https://github.com/unitreerobotics/unitree_dds_wrapper) in the original h1_2 branch was a temporary version. It has now been fully migrated to the official Python-based control and communication library: [unitree_sdk2_python](https://github.com/unitreerobotics/unitree_sdk2_python).
>
> **Note 3**: All identifiers in front of the command are meant for prompting: **Which device and directory the command should be executed on**.
>
> In the Ubuntu system's `~/.bashrc` file, the default configuration is: `PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '`
>
> Taking the command `(tv) unitree@Host:~$ pip install meshcat` as an example:
>
> - `(tv)` Indicates the shell is in the conda environment named `tv`.
> - `unitree@Host:~` Shows the user `\u` `unitree` is logged into the device `\h` `Host`, with the current working directory `\w` as `$HOME`.
> - `$` shows the current shell is Bash (for non-root users).
> - `pip install meshcat` is the command `unitree` wants to execute on `Host`.
>
> You can refer to [Harley Hahn's Guide to Unix and Linux](https://www.harley.com/unix-book/book/chapters/04.html#H)  and  [Conda User Guide](https://docs.conda.io/projects/conda/en/latest/user-guide/getting-started.html) to learn more.

# 2. 💻 Simulation Deployment

## 2.1 📥 Environment Setup

First, install [unitree_sim_isaaclab](https://github.com/unitreerobotics/unitree_sim_isaaclab). Follow that repo’s README.

Then launch the simulation with a G1(29 DoF) and Dex3 hand configuration:

```bash
(base) unitree@Host:~$ conda activate unitree_sim_env
(unitree_sim_env) unitree@Host:~$ cd ~/unitree_sim_isaaclab
(unitree_sim_env) unitree@Host:~/unitree_sim_isaaclab$ python sim_main.py --device cpu --enable_cameras --task Isaac-PickPlace-Cylinder-G129-Dex3-Joint --enable_dex3_dds --robot_type g129
```

💥💥💥 NOTICE❗

> **After simulation starts, click once in the window to activate it.**
>
> The terminal will show:  `controller started, start main loop...`

Here is the simulation GUI:

<p align="center">   <a href="https://oss-global-cdn.unitree.com/static/bea51ef618d748368bf59c60f4969a65_1749x1090.png">     <img src="https://oss-global-cdn.unitree.com/static/bea51ef618d748368bf59c60f4969a65_1749x1090.png" alt="Simulation UI" style="width: 75%;">   </a> </p>

## 2.2 🚀 Launch

This program supports XR control of a physical robot or in simulation. Choose modes with command-line arguments:

- **Basic control parameters**

| ⚙️ Parameter |                 📜 Description                 |                          🔘 Options                           | 📌 Default |
| :---------: | :-------------------------------------------: | :----------------------------------------------------------: | :-------: |
| `--xr-mode` |             Choose XR input mode              | `hand` (**hand tracking**)<br/>`controller` (**controller tracking**) |  `hand`   |
|   `--arm`   | Choose robot arm type (see 0. 📖 Introduction) |           `G1_29`<br/>`G1_23`<br/>`H1_2`<br/>`H1`            |  `G1_29`  |
|   `--ee`    |  Choose end-effector (see 0. 📖 Introduction)  |       `dex1`<br/>`dex3`<br/>`inspire1`<br />`brainco`        |   none    |

- **Mode flags**

|    ⚙️ Flag    |                        📜 Description                         |
| :----------: | :----------------------------------------------------------: |
|  `--record`  | Enable **data recording**<br />After pressing **r** to start, press **s** to start/stop saving an episode. Can repeat. |
|  `--motion`  | Enable **motion mode**<br />After enabling this mode, the teleoperation program can run alongside the robot's motion control.<br />In **hand tracking** mode, you can use the [R3 Controller](https://www.unitree.com/cn/R3) to control the robot's walking behavior; <br />in **controller tracking** mode, you can also use [controllers to control the robot’s movement](https://github.com/unitreerobotics/xr_teleoperate/blob/375cdc27605de377c698e2b89cad0e5885724ca6/teleop/teleop_hand_and_arm.py#L247-L257). |
| `--headless` |        Run without GUI (for headless PC2 deployment)         |
|   `--sim`    |                  Enable **simulation mode**                  |

Assuming hand tracking with G1(29 DoF) + Dex3 in simulation with recording:

```bash
(tv) unitree@Host:~$ cd ~/xr_teleoperate/teleop/
(tv) unitree@Host:~/xr_teleoperate/teleop/$ python teleop_hand_and_arm.py --xr-mode=hand --arm=G1_29 --ee=dex3 --sim --record
# Simplified (defaults apply):
(tv) unitree@Host:~/xr_teleoperate/teleop/$ python teleop_hand_and_arm.py --ee=dex3 --sim --record
```

After the program starts, the terminal shows:

<p align="center">   <a href="https://oss-global-cdn.unitree.com/static/735464d237214f6c9edf8c7db9847a0a_1874x1275.png">     <img src="https://oss-global-cdn.unitree.com/static/735464d237214f6c9edf8c7db9847a0a_1874x1275.png" alt="Terminal Start Log" style="width: 75%;">   </a> </p>

Next steps:

1. Wear your XR headset (e.g. Apple Vision Pro, PICO4, etc.)

2. Connect to the corresponding Wi‑Fi

3. Open a browser (e.g. Safari or PICO Browser) and go to:  `https://192.168.123.2:8012?ws=wss://192.168.123.2:8012`

   > **Note 1**: This IP must match your **Host** IP (check with `ifconfig`).
   >
   > **Note 2**: You may see a warning page. Click **Advanced**, then **Proceed to IP (unsafe)**.

   <p align="center">
     <a href="https://oss-global-cdn.unitree.com/static/cef18751ca6643b683bfbea35fed8e7c_1279x1002.png">
       <img src="https://oss-global-cdn.unitree.com/static/cef18751ca6643b683bfbea35fed8e7c_1279x1002.png" alt="vuer_unsafe" style="width: 50%;">
     </a>
   </p>

4. In the Vuer web, click **Virtual Reality**. Allow all prompts to start the VR session.

   <p align="center">  <a href="https://oss-global-cdn.unitree.com/static/fdeee4e5197f416290d8fa9ecc0b28e6_2480x1286.png">    <img src="https://oss-global-cdn.unitree.com/static/fdeee4e5197f416290d8fa9ecc0b28e6_2480x1286.png" alt="Vuer UI" style="width: 75%;">  </a> </p>

5. You’ll see the robot’s first-person view in the headset. The terminal prints connection info:

   ```bash
   websocket is connected. id:dbb8537d-a58c-4c57-b49d-cbb91bd25b90
   default socket worker is up, adding clientEvents
   Uplink task running. id:dbb8537d-a58c-4c57-b49d-cbb91bd25b90
   ```

6. Align your arm to the **robot’s initial pose** to avoid sudden movements at start:

   <p align="center">  <a href="https://oss-global-cdn.unitree.com/static/2522a83214744e7c8c425cc2679a84ec_670x867.png">    <img src="https://oss-global-cdn.unitree.com/static/2522a83214744e7c8c425cc2679a84ec_670x867.png" alt="Initial Pose" style="width: 25%;">  </a> </p>

7. Press **r** in the terminal to begin teleoperation. You can now control the robot arm and dexterous hand.

8. During teleoperation, press **s** to start recording; press **s** again to stop and save. Repeatable process.

<p align="center">  <a href="https://oss-global-cdn.unitree.com/static/f5b9b03df89e45ed8601b9a91adab37a_2397x1107.png">    <img src="https://oss-global-cdn.unitree.com/static/f5b9b03df89e45ed8601b9a91adab37a_2397x1107.png" alt="Recording Process" style="width: 75%;">  </a> </p>

> **Note 1**: Recorded data is stored in `xr_teleoperate/teleop/utils/data` by default, with usage instructions at this repo:  [unitree_IL_lerobot](https://github.com/unitreerobotics/unitree_IL_lerobot/tree/main?tab=readme-ov-file#data-collection-and-conversion).
>
> **Note 2**: Please pay attention to your disk space size during data recording.

## 2.3 🔚 Exit

Press **q** in the terminal (or “record image” window) to quit.



# 3. 🤖 Physical Deployment

Physical deployment steps are similar to simulation, with these key differences:

## 3.1 🖼️ Image Service

In the simulation environment, the image service is automatically enabled. For physical deployment, you need to manually start the image service based on your specific camera hardware. The steps are as follows:

Copy `image_server.py` in the `xr_teleoperate/teleop/image_server` directory to the **Development Computing Unit PC2** of Unitree Robot (G1/H1/H1_2/etc.), 

```bash
# p.s. You can transfer image_server.py to PC2 via the scp command and then use ssh to remotely login to PC2 to execute it.
# Assuming the IP address of the development computing unit PC2 is 192.168.123.164, the transmission process is as follows:
# log in to PC2 via SSH and create the folder for the image server
(tv) unitree@Host:~$ ssh unitree@192.168.123.164 "mkdir -p ~/image_server"
# Copy the local image_server.py to the ~/image_server directory on PC2
(tv) unitree@Host:~$ scp ~/xr_teleoperate/teleop/image_server/image_server.py unitree@192.168.123.164:~/image_server/
```

and execute the following command **in the PC2**:

```bash
# p.s. Currently, this image transmission program supports two methods for reading images: OpenCV and Realsense SDK. Please refer to the comments in the `ImageServer` class within `image_server.py` to configure your image transmission service according to your camera hardware.
# Now located in Unitree Robot PC2 terminal
unitree@PC2:~/image_server$ python image_server.py
# You can see the terminal output as follows:
# {'fps': 30, 'head_camera_type': 'opencv', 'head_camera_image_shape': [480, 1280], 'head_camera_id_numbers': [0]}
# [Image Server] Head camera 0 resolution: 480.0 x 1280.0
# [Image Server] Image server has started, waiting for client connections...
```

After image service is started, you can use `image_client.py` **in the Host** terminal to test whether the communication is successful:

```bash
(tv) unitree@Host:~/xr_teleoperate/teleop/image_server$ python image_client.py
```

## 3.2 ✋ Inspire Hand Service (optional)

> **Note 1**: Skip this if your config does not use the Inspire hand.
>
> **Note 2**: For G1 robot with [Inspire DFX hand](https://support.unitree.com/home/zh/G1_developer/inspire_dfx_dexterous_hand), related issue [#46](https://github.com/unitreerobotics/xr_teleoperate/issues/46).
>
> **Note 3**: For [Inspire FTP hand]((https://support.unitree.com/home/zh/G1_developer/inspire_ftp_dexterity_hand)), related issue [#48](https://github.com/unitreerobotics/xr_teleoperate/issues/48).

First, use [this URL: DFX_inspire_service](https://github.com/unitreerobotics/DFX_inspire_service) to clone the dexterous hand control interface program. And Copy it to **PC2** of  Unitree robots. 

On Unitree robot's **PC2**, execute command:

```bash
unitree@PC2:~$ sudo apt install libboost-all-dev libspdlog-dev
# Build project
unitree@PC2:~$ cd DFX_inspire_service && mkdir build && cd build
unitree@PC2:~/DFX_inspire_service/build$ cmake ..
unitree@PC2:~/DFX_inspire_service/build$ make -j6

# (For unitree g1) Terminal 1.
unitree@PC2:~/DFX_inspire_service/build$ sudo ./inspire_g1
# or (For unitree h1) Terminal 1.
unitree@PC2:~/DFX_inspire_service/build$ sudo ./inspire_h1 -s /dev/ttyUSB0

# Terminal 2. Run example
unitree@PC2:~/DFX_inspire_service/build$ ./hand_example
```

If two hands open and close continuously, it indicates success. Once successful, close the `./hand_example` program in Terminal 2.

## 3.3 ✋ BrainCo Hand Service (Optional)

Please refer to the [official documentation](https://support.unitree.com/home/en/G1_developer/brainco_hand) for setup instructions.

After installation, you need to manually start the services for both dexterous hands. Example commands are shown below (note: the serial port names may vary depending on your system):

```bash
# Terminal 1.
sudo ./brainco_hand --id 126 --serial /dev/ttyUSB1
# Terminal 2.
sudo ./brainco_hand --id 127 --serial /dev/ttyUSB2
```



## 3.4 🚀 Launch

>  ![Warning](https://img.shields.io/badge/Warning-Important-red)
>
> 1. Everyone must keep a safe distance from the robot to prevent any potential danger!
> 2. Please make sure to read the [Official Documentation](https://support.unitree.com/home/zh/Teleoperation) at least once before running this program.
> 3. Without `--motion`, always make sure that the robot has entered [debug mode (L2+R2)](https://support.unitree.com/home/zh/H1_developer/Remote_control) to stop the motion control program, this will avoid potential command conflict problems.
> 4. To use motion mode (with `--motion`), ensure the robot is in control mode (via [R3 remote](https://www.unitree.com/R3)).
> 5. In motion mode:
>    - Right controller **A** = Exit teleop
>    - Both joysticks pressed = soft emergency stop (switch to damping mode)
>    - Left joystick = drive directions; 
>    - right joystick = turning; 
>    - max speed is limited in the code.

Same as simulation but follow the safety warnings above.

## 3.5 🔚 Exit

> ![Warning](https://img.shields.io/badge/Warning-Important-red)
>
> To avoid damaging the robot, it is recommended to position the robot's arms close to the initial pose before pressing **q** to exit.
>
> - In **Debug Mode**: After pressing the exit key, both arms will return to the robot's **initial pose** within 5 seconds, and then the control will end.
>
> - In **Motion Mode**: After pressing the exit key, both arms will return to the robot's **motion control pose** within 5 seconds, and then the control will end.

Same as simulation but follow the safety warnings above.



# 4. 🗺️ Codebase Overview

```
xr_teleoperate/
│
├── assets                    [Storage of robot URDF-related files]
│
├── hardware                  [3D‑printed hardware modules]
│
├── teleop
│   ├── image_server
│   │     ├── image_client.py      [Used to receive image data from the robot image server]
│   │     ├── image_server.py      [Capture images from cameras and send via network (Running on robot's Development Computing Unit PC2)]
│   │
│   ├── televuer
│   │      ├── src/televuer
│   │         ├── television.py       [captures XR devices's head, wrist, hand/controller data]
│   │         ├── tv_wrapper.py       [Post-processing of captured data]
│   │      ├── test
│   │         ├── _test_television.py [test for television.py]
│   │         ├── _test_tv_wrapper.py [test for tv_wrapper.py]
│   │
│   ├── robot_control
│   │      ├── src/dex-retargeting [Dexterous hand retargeting algorithm library]
│   │      ├── robot_arm_ik.py     [Inverse kinematics of the arm]
│   │      ├── robot_arm.py        [Control dual arm joints and lock the others]
│   │      ├── hand_retargeting.py [Dexterous hand retargeting algorithm library Wrapper]
│   │      ├── robot_hand_inspire.py  [Control inspire hand joints]
│   │      ├── robot_hand_unitree.py  [Control unitree hand joints]
│   │
│   ├── utils
│   │      ├── episode_writer.py          [Used to record data for imitation learning]
│   │      ├── weighted_moving_filter.py  [For filtering joint data]
│   │      ├── rerun_visualizer.py        [For visualizing data during recording]
│   │
│   └── teleop_hand_and_arm.py    [Startup execution code for teleoperation]
```

# 5. 🛠️ Hardware

please see [Device document](Device.md).



# 6. 🙏 Acknowledgement

This code builds upon following open-source code-bases. Please visit the URLs to see the respective LICENSES:

1. https://github.com/OpenTeleVision/TeleVision
2. https://github.com/dexsuite/dex-retargeting
3. https://github.com/vuer-ai/vuer
4. https://github.com/stack-of-tasks/pinocchio
5. https://github.com/casadi/casadi
6. https://github.com/meshcat-dev/meshcat-python
7. https://github.com/zeromq/pyzmq
8. https://github.com/Dingry/BunnyVisionPro
9. https://github.com/unitreerobotics/unitree_sdk2_python
