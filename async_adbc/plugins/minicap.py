import os
# import pkg_resources
from importlib import resources
from async_adbc.plugin import Plugin


class MinicapPlugin(Plugin):
    PUSH_TO = "/data/local/tmp"

    async def init(self):
        """
        初始化minicap
        """
        with resources.path('async_adbc','vendor') as path:
            MINICAP_LIBS = os.path.join(path,"minicap")


        exists = await self._device.file_exists("/data/local/tmp/minicap")
        exists = exists and await self._device.file_exists(
            "/data/local/temp/minicap.so"
        )
        if exists:
            return

        props = await self._device.properties
        abi = props.get("ro.product.cpu.abi", "unknow")
        pre_sdk = props.get("ro.build.version.preview_sdk", "unknow")
        rel_sdk = props.get("ro.build.version.release", "unknow")
        sdk = props.get("ro.build.version.sdk")
        sdk = int(sdk or 0)

        if pre_sdk.isdigit() and int(pre_sdk) > 0:
            sdk += 1

        if sdk >= 16:
            binfile = "minicap"
        else:
            binfile = "minicap-nopie"
        binfile_path = os.path.join(MINICAP_LIBS, abi, binfile)

        if not os.path.exists(binfile_path):
            raise FileNotFoundError(binfile_path, "没有与该设备匹配的minicap")

        await self._device.push(binfile_path, self.PUSH_TO + "/minicap", chmode=0o755)

        sofile_path = os.path.join(
            MINICAP_LIBS, f"minicap-shared/aosp/libs/android-{sdk}/{abi}/minicap.so"
        )

        if not os.path.isfile(sofile_path):
            sofile_path = os.path.join(
                MINICAP_LIBS,
                f"minicap-shared/aosp/libs/android-{rel_sdk}/{abi}/minicap.so",
            )

        await self._device.push(sofile_path, self.PUSH_TO + "/minicap.so", chmode=0o755)

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
            
        
    