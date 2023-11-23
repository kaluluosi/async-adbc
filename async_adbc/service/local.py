import asyncio
import os
import struct

from asyncio import StreamReader
from stat import S_IFREG
from typing import Callable, List, Literal, Optional, Union
from pydantic import BaseModel
from async_adbc.protocol import DATA, DONE, FAIL, RECV, SEND, Connection
from async_adbc.service import Service

ProgressCallback = Callable[[str, int, int], None]


class ReverseRule(BaseModel):
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
        double-quotes. Arguments cannot contain double quotes or things
        will go very wrong.
        Note that this is the non-interactive version of "adb shell"

        Args:
            cmd (str): 命令

        Returns:
            str: 返回打印
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

        NOTE: 属于底层方法，你可以用 `shell_raw` 返回的 `Response`获得 `Reader`，效果是一样的。

        WARNING: `reader` 需要手动关闭。

        Args:
            cmd (str): 命令

        Returns:
            StreamReader: 读取器
        """

        args = map(str, args)
        cmd = " ".join([cmd, *args])
        res = await self.request("shell", cmd)
        return res.reader

    async def adbd_tcpip(self, port: int) -> str:
        """
        开启adbd远程调试端口

        等同于： adb tcpip <port>

        Args:
            port (int): 端口

        Raises:
            RuntimeError: _description_

        Returns:
            str: 返回打印
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

        Raises:
            RuntimeError: 启动失败
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

        Raises:
            RuntimeError: 启动失败
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
        option: Literal[
            "bootloader", "recovery", "sideload", "sideload-auto-reboot", ""
        ] = "",
    ):
        """
        重启设备

        Args:
            wait_for (bool, optional): 是否等待重启. Defaults to True.
            timeout (int, optional): 等待超时，单位秒. Defaults to 60.
            wait_interval (int, optional): 等待间隔，单位秒. Defaults to 1.
            option (Optional[Literal[&quot;bootloader&quot;,&quot;recovery&quot;,&quot;sideload&quot;,&quot;sideload, optional): `reboot:`命令的额外参数，对应`adb reboot <option>`. Defaults to None.

        Raises:
            TimeoutError: 超过timeout都没有重启完毕时抛出
        """

        await self.request("reboot", option)

        if not wait_for:
            return

        # wait shutdown
        await self.wait_shutdown(timeout, wait_interval)

        # wait startup and launcher inited
        await self.wait_boot_complete(timeout, wait_interval)

    async def wait_shutdown(self, timeout, wait_interval):
        """
        等待设备关机

        Args:
            timeout (int): 等待超时，单位秒
            wait_interval (int): 等待间隔，单位秒

        Raises:
            TimeoutError: 超过timeout都没有关闭完毕时抛出
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

        Args:
            timeout (int, optional): 等待超时，单位秒. Defaults to 60.
            wait_interval (int, optional): 等待间隔，单位秒. Defaults to 1.

        Raises:
            TimeoutError: 超过timeout都没有重启完毕时抛出
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
        conn.close()

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
                    conn.close()
                    return
                elif flag == FAIL:
                    error = await _read_data(conn)
                    raise RuntimeError(error.decode())

    async def reverse_list(self) -> List[ReverseRule]:
        """列出当前设备的反向代理规则列表

        返回的一定是当前设备的代理规则。

        等同于：adb reverse --list

        Returns:
            list[ReverseRule]: 反向代理列表
        """
        res = await self.request("reverse", "list-forward")
        reverses: list[ReverseRule] = []

        with res:
            res = await res.text()
            lines = res.splitlines()

        for line in lines:
            if not line:
                continue

            _type, remote, local = line.split()
            reverses.append(ReverseRule(type=_type, local=remote, remote=local))

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
            res = await self.request(
                "reverse", "forward", "norebind", f"{local};{remote}"
            )
        else:
            res = await self.request("reverse", "forward", f"{local};{remote}")

        res.close()

    async def reverse_remove(self, local: Union[str, ReverseRule]):
        """移除反向代理

        等同于：adb reverse --remove

        Args:
            remote (str): 设备本地端口
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
