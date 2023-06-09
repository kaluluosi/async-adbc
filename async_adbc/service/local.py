from asyncio import StreamReader
from dataclasses import dataclass
import os
from stat import S_IFREG
import struct
from typing import Callable, Optional

from dataclasses_json import dataclass_json
from async_adbc.protocol import DATA, DONE, FAIL, RECV, SEND, Connection
from async_adbc.service import Service

ProgressCallback = Callable[[str, int, int], None]


@dataclass_json
@dataclass
class ReverseRule:
    type: str
    local: str
    remote: str


class LocalService(Service):
    TEMP_PATH = "/data/local/tmp"
    DEFAULT_CHMOD = 0o644
    DATA_MAX_LENGTH = 65536

    async def shell_raw(self, cmd: str, *args) -> bytes:
        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        res = await res.reader.read()
        return res

    async def shell(self, cmd: str, *args: str) -> str:
        """
        调用安卓设备的shell命令

        等同于：adb shell

        Run 'command arg1 arg2 ...' in a shell on the device, and return
        its output and error streams. Note that arguments must be separated
        by spaces. If an argument contains a space, it must be quoted with
        double-quotes. Arguments cannot contain double quotes or things
        will go very wrong.
        Note that this is the non-interactive version of "adb shell"

            Args:
                cmd (str): _description_

            Returns:
                str: _description_
        """
        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        res = await res.reader.read()
        return res.decode().strip()

    async def shell_reader(self, cmd: str, *args) -> StreamReader:
        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        return res.reader

    async def adbd_tcpip(self, port: int) -> str:
        """开启adbd远程调试端口

        等同于： adb tcpip <port>

        Args:
            port (int): _description_

        Returns:
            str: _description_
        """

        res = await self.request("tcpip", port)
        ret = await res.reader.read()
        ret = ret.decode().strip()

        if "restarting in TCP mode port" not in ret:
            raise RuntimeError(ret)

        return ret

    async def adbd_root(self) -> str:
        res = await self.request("root")
        ret = await res.reader.read()
        ret = ret.decode().strip()

        if "restarting adbd as root" not in ret:
            raise RuntimeError(ret)

        return ret

    async def adbd_unroot(self) -> str:
        res = await self.request("unroot")
        ret = await res.reader.read()
        ret = ret.decode().strip()

        if "restarting adbd as non root" not in ret:
            raise RuntimeError(ret)

        return ret

    async def reboot(self, option: str = ""):
        """重启

        等同于：adb reboot

        Args:
            option (str): [bootloader|recovery|sideload|sideload-auto-reboot]

        Returns:
            _type_: _description_
        """

        res = await self.request("reboot", option)

    async def remount(self):
        """
        remount 是一种 adb 命令，用于请求 adbd 将设备的文件系统重新挂载为可读写模式，而不是只读模式。
        默认情况 /system 目录是只读的，非root用户无权限写入，remount就是重新挂载未可写。
        通常，在执行 "adb sync" 或 "adb push" 请求之前，都需要使用这种命令。
        但是，由于非root设备不允许这种操作，所以这种请求可能无法成功。


        等同于： adb remount

        Ask adbd to remount the device's filesystem in read-write mode,
        instead of read-only. This is usually necessary before performing
        an "adb sync" or "adb push" request.
        This request may not succeed on certain builds which do not allow
        that.
        """
        res = await self.request("remount:")
        ret = await res.reader.read()
        ret = ret.decode()
        if "remount succeeded" not in ret:
            raise RuntimeError(ret)

        return ret

    async def push(
        self,
        src: str,
        dst: str,
        chmode: int = DEFAULT_CHMOD,
        progress_cb: Optional[ProgressCallback] = None,
    ):
        """
        推送src文件到设备dest文件路径。

        如果这个文件的父目录不存在，也会自动帮其创建父目录。
        只支持文件，不支持目录。

        等同于：adb push src dst

        Args:
            src (str): 文件路径
            dst (str): 目标文件路径，不可以是文件夹
            chmode (int, optional): 文件权限. Defaults to DEFAULT_CHMOD.
            progress_cb (Optional[ProgressCallback], optional): 进度回调. Defaults to None.
        """

        if not os.path.exists(src) or os.path.isdir(src):
            raise FileNotFoundError(f"src:{src} 路径不存在或不是文件")

        # 推送流程是独立控制的不是请求响应流程，因此不能用 self.reqeust方法

        conn = await self.create_connection()
        await conn.request("sync:")

        stat = os.stat(src)
        timestamp = int(stat.st_mtime)
        size = stat.st_size
        has_send = 0
        chmode = chmode | S_IFREG
        args = f"{dst},{chmode}".encode()

        await conn.message(SEND, data=args)

        with open(src, "rb") as stream:
            while True:
                chunk = stream.read(self.DATA_MAX_LENGTH)
                if not chunk:
                    break
                chunk_size = len(chunk)
                has_send += chunk_size

                await conn.message(DATA, data=chunk)

                if progress_cb:
                    progress_cb(src, size, has_send)

        await conn.message(DONE, timestamp)
        await conn._check_status()

    async def pull(self, src: str, dst: str):
        """从设备的src路径拉取文件保存到本地的dest路径。只支持文件，不支持拉整个目录。

        等同于：adb pull

        Args:
            src (str): 设备上的文件路径
            dst (str): 本地保存的路径

        Raises:
            RuntimeError: 请求失败
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
        await conn.message(RECV, data=b_src)

        with open(dst, "wb") as stream:
            while True:
                flag = await conn.reader.read(4)
                flag = flag.decode()
                if flag == DATA:
                    data = await _read_data(conn)
                    stream.write(data)
                elif flag == DONE:
                    await conn.reader.read(4)
                    return
                elif flag == FAIL:
                    error = await _read_data(conn)
                    raise RuntimeError(error.decode())

    async def reverse_list(self) -> list[ReverseRule]:
        """列出当前设备的反向代理规则列表

        返回的一定是当前设备的代理规则。

        等同于：adb reverse --list

        Returns:
            list[ReverseRule]: 反向代理列表
        """
        res = await self.request("reverse", "list-forward")
        reverses: list[ReverseRule] = []

        res = await res.text()
        lines = res.splitlines()

        for line in lines:
            if not line:
                continue

            _type, remote, local = line.split()
            reverses.append(ReverseRule(_type, remote, local))

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

        Args:
            remote (str): _description_
            local (str): _description_
            norebind (bool, optional): _description_. Defaults to False.
        """

        if norebind:
            await self.request("reverse", "forward", "norebind", f"{local};{remote}")
        else:
            await self.request("reverse", "forward", f"{local};{remote}")

    async def reverse_remove(self, local: str | ReverseRule):
        """移除反向代理

        等同于：adb reverse --remove

        Args:
            remote (str): 设备本地端口
        """
        if isinstance(local, ReverseRule):
            local = local.local

        await self.request("reverse", "killforward", local)

    async def reverse_remove_all(self):
        """移除所有反向代理规则

        等同于：adb reverse --remove-all
        """
        await self.request("reverse", "killforward-all")
