import os
from async_adbc.plugin import Plugin, register_plugin


@register_plugin("minicap", "minicap")
class MinicapPlugin(Plugin):
    PUSH_TO = "/data/local/tmp"

    async def init(self, force: bool = False):
        """
        初始化minicap
        """
        try:
            from importlib.resources import files, as_file
        except ImportError:
            from importlib_resources import files, as_file

        exists = await self._device.file_exists("/data/local/tmp/minicap")
        exists = exists and await self._device.file_exists(
            "/data/local/tmp/minicap.so"
        )
        if exists and not force:
            return

        props = await self._device.get_properties()
        # 优先获取64位abi
        abi = props.get("ro.product.cpu.abi64") or props.get("ro.product.cpu.abi", "unknown")
        pre_sdk = props.get("ro.build.version.preview_sdk", "unknown")
        rel_sdk = props.get("ro.build.version.release", "unknown")
        sdk = props.get("ro.build.version.sdk")
        sdk = int(sdk or 0)

        if pre_sdk.isdigit() and int(pre_sdk) > 0:
            sdk += 1

        if sdk >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"

        # 用官方最佳实践 importlib.resources 定位 vendor 目录
        minicap_traversable = files("async_adbc") / "vendor" / "minicap"
        binfile_traversable = minicap_traversable / abi / binfile

        # 推送 minicap 二进制文件
        with as_file(binfile_traversable) as binfile_path:
            if not os.path.exists(binfile_path):
                raise FileNotFoundError(binfile_path, "没有与该设备匹配的minicap")

            await self._device.push(binfile_path, self.PUSH_TO + "/minicap", chmod=0o755)

        # 直接用 abi 目录下的 minicap.so
        sofile_traversable = minicap_traversable / abi / "minicap.so"

        # 推送 minicap.so
        with as_file(sofile_traversable) as sofile_path:
            await self._device.push(sofile_path, self.PUSH_TO + "/minicap.so", chmod=0o755)

    async def get_frame(self)->bytes:
        """
        获取当前屏幕帧截图

        Raises:
            RuntimeError: CANNOT LINK EXECUTABLE
            RuntimeError: naccessible or not found

        Returns:
            bytes: jpg格式字节
        """
        
        await self.init()

        resolution = await self._device.wm.size()
        size = resolution.physical_size
        orientation = await self._device.wm.orientation()
        raw_data = await self._device.shell_raw(
            "LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap",
            "-P",
            f"{size}@{size}/{orientation}",
            "-s",
        )

        if b"CANNOT LINK EXECUTABLE" in raw_data:
            raise RuntimeError(raw_data.decode(),"CANNOT LINK EXECUTABLE")

        if b"inaccessible or not found" in raw_data:
            raise RuntimeError(raw_data.decode(),"inaccessible or not found")

        return raw_data

    async def screencap(self, filename="screencap.jpg"):
        """
        截图保存到本地

        Args:
            filename (str, optional): 保存的文件名. Defaults to "screencap.jpg".
        """
        frame_data = await self.get_frame()
        
        with open(filename, "wb") as f:
            f.write(frame_data)
            
        
    