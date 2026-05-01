import asyncio
import os
import struct

from asyncio import StreamReader
from stat import S_IFREG
from typing import Callable, List, Optional, Union
from async_adbc.protocol import Connection, Response
from async_adbc.service.base import Service
from async_adbc.config import TEMP_PATH, DEFAULT_CHMOD, DATA_MAX_LENGTH
from async_adbc.models import ReverseRule


ProgressCallback = Callable[[str, int, int], None]


class LocalService(Service):

    async def shell_raw(self, cmd: str, *args) -> bytes:
        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        with res:
            ret = await res.reader.read()
        return ret

    async def shell(self, cmd: str, *args: str) -> str:
        """
        调用安卓设备的shell命令

        NOTE: 如果命令是持续打印不会退出，比如logcat，那么会导致这个方法无法退出。
        如果需要持续读取打印，应该用 `shell_reader`。

        等同于：adb shell

        Run 'command arg1 arg2 ...' in a shell on the device, and return
        its output and error streams. Note that arguments must be separated
        by spaces. If an argument contains a space, it must be quoted with
        double quotes. Arguments cannot contain double quotes or things
        will go very wrong.
        Note that this is the non-interactive version of "adb shell".
        """
        str_args = map(str, args)
        cmd = " ".join([cmd, *str_args])
        res = await self.request("shell", cmd)
        with res:
            res = await res.reader.read()
            return res.decode().strip()

    async def shell_reader(self, cmd: str, *args) -> StreamReader:
        """
        返回shell的读取器，用来持续读取打印。

        NOTE: 属于底层方法，你可以用 `shell_raw` 返回的 `Response` 获得 `Reader`，效果是一样的。

        WARNING: `reader` 需要手动关闭。
        """

        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        return res.reader

    async def adbd_tcpip(self, port: int) -> str:
        """
        开启adbd远程调试端口

        等同于： adb tcpip <port>
        """

        res = await self.request("tcpip", str(port))
        with res:
            ret = await res.reader.read()
            ret = ret.decode().strip()

        if "restarting in TCP mode port" not in ret:
            raise RuntimeError(ret)

        return ret

    async def adbd_root(self):
        """
        手机端的adbd进程以root权限启动

        NOTE: 这个方法调用后会导致adb短暂无法跟设备通信
        """

        res = await self.request("root:")
        with res:
            ret = await res.reader.read()
            ret = ret.decode().strip()

        if "adbd is already running as root" == ret or "restarting adbd as root" == ret:
            return
        else:
            raise RuntimeError(ret)

    async def adbd_unroot(self):
        """
        手机端的adbd进程取消root权限

        NOTE: 这个方法调用后会导致adb短暂无法跟设备通信
        """
        res = await self.request("unroot:")
        with res:
            ret = await res.reader.read()
            ret = ret.decode().strip()

        if "restarting adbd as non root" == ret or "adbd not running as root" == ret:
            return
        else:
            raise RuntimeError(ret)

    async def reboot(
        self,
        wait_for: bool = True,
        timeout: int = 60,
        wait_interval: int = 1,
        option: Optional[
            Union["Literal['bootloader']", "Literal['recovery']", "Literal['sideload']", "Literal['sideload-auto-reboot']"]
        ] = None,
    ):
        """
        重启设备
        """

        args = ["reboot"]
        if option:
            args.append(option)
        await self.request(*args)

        if not wait_for:
            return

        # wait shutdown
        await self.wait_shutdown(timeout, wait_interval)

        # wait startup and launcher inited
        await self.wait_boot_complete(timeout, wait_interval)

    async def wait_shutdown(self, timeout, wait_interval):
        """
        等待设备关机
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

        # timeout
        raise TimeoutError(
            "等待关机超时，可能关机失败，或者设备关机时间太长设置的等待时间太短。"
        )

    async def wait_boot_complete(self, timeout: int = 60, wait_interval: int = 1):
        """
        等待设备启动完毕
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

        # timeout
        raise TimeoutError(
            "等待重启超时，可能重启失败，或者设备重启时间太长设置的等待时间太短。"
        )

    async def remount(self):
        """
        remount 是一种 adb 命令，用于请求 adbd 将设备的文件系统重新挂载为可读写模式，而不是只读模式。
        默认情况 /system 目录是只读的，非root用户无权限写入，remount就是重新挂载为可写。
        通常，在执行 "adb sync" 或 "adb push" 请求之前，都需要使用这种命令。
        但是，由于非root设备不允许这种操作，所以这种请求可能不会成功。

        等同于： adb remount
        """
        res = await self.request("remount:")

        with res:
            ret = await res.reader.read()
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
        """
        推送src文件到设备dest文件路径。

        如果这个文件的父目录不存在，也会自动帮其创建父目录。
        只支持文件，不支持目录。

        等同于：adb push src dst
        """

        if not os.path.exists(src) or os.path.isdir(src):
            raise FileNotFoundError(f"src:{src} 路径不存在或不是文件")

        # 推送流程是独立控制的不是请求响应流程，所以不能用 self.reqeust 方法

        conn = await self.create_connection()
        await conn.request("sync:")

        stat = os.stat(src)
        timestamp = int(stat.st_mtime)
        size = stat.st_size
        has_send = 0
        chmod = chmod | S_IFREG
        args = f"{dst},{chmod}".encode()

        await conn.message("SEND", data=args)

        with open(src, "rb") as stream:
            while True:
                chunk = stream.read(DATA_MAX_LENGTH)
                if not chunk:
                    break
                chunk_size = len(chunk)
                has_send += chunk_size

                await conn.message("DATA", data=chunk)

                if progress_cb:
                    progress_cb(src, size, has_send)

        await conn.message("DONE", timestamp)
        await conn._check_status()
        conn.close()

    async def pull(self, src: str, dst: str):
        """从设备的src路径拉取文件保存到本地的dest路径。只支持文件，不支持拉整个目录。

        等同于：adb pull
        """

        async def _read_data(conn: Connection):
            length = await conn.reader.read(4)
            length = struct.unpack("<I", length)[0]
            data = bytearray()
            while len(data) < length:
                recv = await conn.reader.read(length - len(data))
                data += recv
            return data

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
        """
        res = await self.request("reverse", "list-forward")
        reverses: list[ReverseRule] = []

        with res:
            res = await res.text()
            lines = res.splitlines()

        for line in lines:
            if not line:
                continue

            type, remote, local = line.split()
            reverses.append(ReverseRule(type=type, local=remote, remote=local))

        return reverses

    async def reverse(self, remote: str, local: str, norebind: bool = False):
        """反向代理

        注意：
        由于代理关系是反向的，所以<local>相当于设备的端口，<remote>相当于adb server的主机端口。

        Note that in this case, <local> corresponds to the socket on the device
        and <remote> corresponds to the socket on the host.

        the format of <local> is one of:
            tcp:<port>      -> TCP connection on localhost:<port>
            local:<path>    -> Unix local domain socket on <path>
        the format of <remote> is one of:
            tcp:<port>      -> TCP localhost:<port> on device
            local:<path>    -> Unix local domain socket on device
            jdwp:<pid>      -> JDWP thread on VM process <pid>
            vsock:<CID>:<port> -> vsock on the given CID and port
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

        等同于：adb reverse --remove
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
