# 版权信息
#
# © [2025] LimX Dynamics Technology Co., Ltd. 保留所有权利。

"""图像服务模块

注意：
- ImageServer (image_server.py) - 在机器人端运行，依赖 ROS2
- ImageClient (image_client.py) - 在主控端运行，无 ROS2 依赖

为避免导入冲突，不在此处自动导入，请直接使用：
    from image_service.image_client import ImageClient  (主控端)
    from image_service.image_server import ImageBridge  (机器人端)
"""

__all__ = ['ImageClient']

# 延迟导入，避免 ROS2 依赖冲突
def __getattr__(name):
    if name == 'ImageClient':
        from .image_client import ImageClient
        return ImageClient
    elif name == 'ImageServer':
        from .image_server import ImageBridge
        return ImageBridge
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
