"""Local 服务集成测试模块"""
import pytest
import tempfile
import os

from async_adbc.client import ADBClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestLocalServiceIntegration:
    """测试 LocalService 集成"""

    async def test_shell(self):
        """测试 shell 命令"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            result = await device.shell("echo hello world")
            assert "hello world" in result
        finally:
            device.close()
            adbc.close()

    async def test_shell_raw(self):
        """测试 shell_raw 命令"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            result = await device.shell_raw("echo hello world")
            assert b"hello world" in result
        finally:
            device.close()
            adbc.close()

    async def test_get_properties(self):
        """测试获取设备属性"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            props = await device.get_properties()
            assert isinstance(props, dict)
            # 检查一些常见属性
            assert "ro.build.version.release" in props or "ro.build.version.sdk" in props
        finally:
            device.close()
            adbc.close()

    async def test_file_exists(self):
        """测试文件存在判断"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            # /system 应该存在
            exists = await device.file_exists("/system")
            assert exists is True
        finally:
            device.close()
            adbc.close()

    async def test_push_pull(self):
        """测试文件推送和拉取"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        # 创建临时测试文件
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = "test file content for async-adbc integration test"
            f.write(test_content)
            local_path = f.name

        pull_path = None
        remote_path = "/data/local/tmp/test_async_adbc.txt"
        try:
            # 推送到设备
            await device.push(local_path, remote_path)

            # 验证文件存在
            exists = await device.file_exists(remote_path)
            assert exists is True

            # 拉取回来
            pull_path = local_path + ".pulled"
            await device.pull(remote_path, pull_path)

            # 验证内容一致
            with open(pull_path, "r") as f:
                pulled_content = f.read()
                assert pulled_content == test_content

        finally:
            device.close()
            adbc.close()
            # 清理
            if os.path.exists(local_path):
                os.unlink(local_path)
            if pull_path and os.path.exists(pull_path):
                os.unlink(pull_path)
            # 清理设备上的文件
            try:
                adbc2 = ADBClient()
                dev2 = await adbc2.device("emulator-5554")
                await dev2.shell(f"rm {remote_path}")
                dev2.close()
                adbc2.close()
            except Exception:
                pass
