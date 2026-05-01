import asyncio
import os
import struct

from asyncio import StreamReader
from stat import S_IFREG
from typing import Callable, List, Optional, Union

from async_adbc.protocol.connection import Connection, Response
from async_adbc.service.base import Service
from async_adbc.config import TEMP_PATH, DEFAULT_CHMOD, DATA_MAX_LENGTH
from async_adbc.models import ReverseRule


ProgressCallback = Callable[[str, int, int], None]


class LocalService(Service):
    """Local 服务，提供与设备 adbd 进程交互的功能"""

    async def shell_raw(self, cmd: str, *args) -> bytes:
        """调用 Android 设备的 shell 命令，返回原始字节

        Args:
            cmd: 命令
            *args: 命令参数

        Returns:
            bytes: 原始输出
        """
        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        with res:
            return await res.read()

    async def shell(self, cmd: str, *args: str) -> str:
        """调用 Android 设备的 shell 命令

        注意：如果命令是持续打印不会退出，比如 logcat，那么会导致这个方法无法退出。
        如果需要持续读取打印，应该用 shell_reader。

        等同于：adb shell

        Args:
            cmd: 命令
            *args: 命令参数

        Returns:
            str: 输出文本
        """
        str_args = map(str, args)
        cmd = " ".join([cmd, *str_args])
        res = await self.request("shell", cmd)
        with res:
            res = await res.read()
            return res.decode().strip()

    async def shell_reader(self, cmd: str, *args) -> StreamReader:
        """返回 shell 的读取器，用来持续读取打印

        注意：属于底层方法，你可以用 shell_raw 返回的 Response 来获取 Reader，效果是一样的。
        警告：reader 需要手动关闭。

        Args:
            cmd: 命令
            *args: 命令参数

        Returns:
            StreamReader: 异步读取器
        """
        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        return res.reader

    async def adbd_tcpip(self, port: int) -> str:
        """开启 adbd 远程调试端口

        等同于：adb tcpip <port>

        Args:
            port: 端口

        Returns:
            str: 返回信息
        """
        res = await self.request("tcpip", str(port))
        with res:
            ret = await res.read()
            ret = ret.decode().strip()

        if "restarting in TCP mode port" not in ret:
            raise RuntimeError(ret)

        return ret

    async def adbd_root(self):
        """让设备上的 adbd 进程以 root 权限启动

        注意：这个方法调用后会导致 ADB 短暂无法与设备通信
        """
        res = await self.request("root:")
        with res:
            ret = await res.read()
            ret = ret.decode().strip()

        if ret not in ["adbd is already running as root", "restarting adbd as root"]:
            raise RuntimeError(ret)

    async def adbd_unroot(self):
        """让设备上的 adbd 进程取消 root 权限

        注意：这个方法调用后会导致 ADB 短暂无法与设备通信
        """
        res = await self.request("unroot:")
        with res:
            ret = await res.read()
            ret = ret.decode().strip()

        if ret not in ["restarting adbd as non root", "adbd not running as root"]:
            raise RuntimeError(ret)

    async def reboot(
        self,
        wait_for: bool = True,
        timeout: int = 60,
        wait_interval: int = 1,
        option: Optional[str] = None,
    ):
        """重启设备

        Args:
            wait_for: 是否等待重启完成
            timeout: 超时时间（秒）
            wait_interval: 等待间隔（秒）
            option: 重启选项，可选 bootloader、recovery、sideload、sideload-auto-reboot
        """
        args = ["reboot"]
        if option:
            args.append(option)
        await self.request(*args)

        if not wait_for:
            return

        await self.wait_shutdown(timeout, wait_interval)
        await self.wait_boot_complete(timeout, wait_interval)

    async def wait_shutdown(self, timeout, wait_interval):
        """等待设备关机

        Args:
            timeout: 超时时间（秒）
            wait_interval: 等待间隔（秒）
        """
        while timeout:
            try:
                res = await self.shell("dumpsys window windows|grep launcher")
                if "launcher" in res:
                    continue
            except Exception:
                return

            await asyncio.sleep(wait_interval)
            timeout -= 1

        raise TimeoutError("等待关机超时，可能关机失败，或者设备关机时间太长")

    async def wait_boot_complete(self, timeout: int = 60, wait_interval: int = 1):
        """等待设备启动完成

        Args:
            timeout: 超时时间（秒）
            wait_interval: 等待间隔（秒）
        """
        while timeout:
            try:
                res = await self.shell("dumpsys window windows|grep launcher")
                if "launcher" in res:
                    return
            except Exception:
                pass

            await asyncio.sleep(wait_interval)
            timeout -= 1

        raise TimeoutError("等待重启超时，可能重启失败，或者设备重启时间太长")

    async def remount(self):
        """重新挂载系统分区为可读写

        remount 是一种 adb 命令，用于请求 adbd 将设备的文件系统重新挂载为可读写模式，而不是只读模式。
        默认情况 /system 目录是只读的，非 root 用户无权限写入，remount 就是重新挂载为可写。
        通常，在执行 adb sync 或 adb push 请求之前，都需要使用这种命令。
        但是，由于非 root 设备不允许这种操作，所以这种请求可能不会成功。

        等同于：adb remount
        """
        res = await self.request("remount:")

        with res:
            ret = await res.read()
            ret = ret.decode()

        if "remount succeeded" not in ret:
            raise RuntimeError(ret)

        return ret

    async def push(
        self,
        src: str,
        dst: str,
        chmod: int = DEFAULT_CHMOD,
        progress_cb: Optional[ProgressCallback] = None,
    ):
        """推送本地文件到设备

        如果这个文件的父目录不存在，也会自动帮其创建父目录。
        只支持文件，不支持目录。

        等同于：adb push src dst

        Args:
            src: 源文件路径
            dst: 目标文件路径
            chmod: 文件权限
            progress_cb: 进度回调函数，参数为 (src, total, sent)
        """
        if not os.path.exists(src) or os.path.isdir(src):
            raise FileNotFoundError(f"src:{src} 路径不存在或不是文件")

        conn = await self.create_connection()
        await conn.request("sync:")

        stat = os.stat(src)
        timestamp = int(stat.st_mtime)
        size = stat.st_size
        has_sent = 0
        chmod = chmod | S_IFREG
        args = f"{dst},{chmod}".encode()

        await conn.message("SEND", data=args)

        with open(src, "rb") as stream:
            while True:
                chunk = stream.read(DATA_MAX_LENGTH)
                if not chunk:
                    break
                chunk_size = len(chunk)
                has_sent += chunk_size

                await conn.message("DATA", data=chunk)

                if progress_cb:
                    progress_cb(src, size, has_sent)

        await conn.message("DONE", timestamp)
        await conn._check_status()
        conn.close()

    async def pull(self, src: str, dst: str):
        """从设备拉取文件到本地

        只支持文件，不支持拉整个目录。

        等同于：adb pull src dst

        Args:
            src: 源文件路径
            dst: 目标文件路径
        """

        async def _read_data(conn: Connection) -> bytes:
            length = await conn.reader.read(4)
            length = struct.unpack("<I", length)[0]
            data = bytearray()
            while len(data) < length:
                recv = await conn.reader.read(length - len(data))
                data += recv
            return bytes(data)

        conn = await self.create_connection()
        await conn.request("sync:")
        b_src = src.encode()
        await conn.message("RECV", data=b_src)

        with open(dst, "wb") as stream:
            while True:
                flag = await conn.reader.read(4)
                flag = flag.decode()
                if flag == "DATA":
                    data = await _read_data(conn)
                    stream.write(data)
                elif flag == "DONE":
                    await conn.reader.read(4)
                    conn.close()
                    return
                elif flag == "FAIL":
                    error = await _read_data(conn)
                    raise RuntimeError(error.decode())

    async def reverse_list(self) -> List[ReverseRule]:
        """列出当前设备的反向代理规则列表

        返回的一定是当前设备的代理规则。

        等同于：adb reverse --list

        Returns:
            List[ReverseRule]: 反向代理规则列表
        """
        res = await self.request("reverse", "list-forward")
        reverses = []

        with res:
            res = await res.text()
            lines = res.splitlines()

        for line in lines:
            if line:
                type_, remote, local = line.split()
                reverses.append(ReverseRule(type=type_, local=remote, remote=local))

        return reverses

    async def reverse(self, remote: str, local: str, norebind: bool = False):
        """反向代理

        注意：由于代理关系是反向的，所以 local 相当于设备的端口，remote 相当于 ADB Server 的主机端口。

        等同于：adb reverse <remote> <local>

        Args:
            remote: 远程地址（主机端）
            local: 本地地址（设备端）
            norebind: 是否不重新绑定
        """
        if norebind:
            res = await self.request(
                "reverse", "forward", "norebind", f"{local};{remote}"
            )
        else:
            res = await self.request("reverse", "forward", f"{local};{remote}")

        res.close()

    async def reverse_remove(self, local: Union[str, ReverseRule]):
        """移除反向代理

        等同于：adb reverse --remove <local>

        Args:
            local: 本地地址（设备端）
        """
        if isinstance(local, ReverseRule):
            local = local.local

        res = await self.request("reverse", "killforward", local)
        res.close()

    async def reverse_remove_all(self):
        """移除所有反向代理规则

        等同于：adb reverse --remove-all
        """
        res = await self.request("reverse", "killforward-all")
        res.close()
