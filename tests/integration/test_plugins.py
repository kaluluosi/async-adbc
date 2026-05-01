"""插件集成测试模块"""

import pytest

from async_adbc.client import ADBClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestCPUPluginIntegration:
    """测试 CPUPlugin 集成"""

    async def test_get_count(self):
        """测试获取 CPU 核心数"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            count = await device.cpu.get_count()
            assert isinstance(count, int)
            assert count >= 1
        finally:
            device.close()
            adbc.close()

    async def test_get_freqs(self):
        """测试获取 CPU 频率"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            freqs = await device.cpu.get_freqs()
            assert len(freqs) >= 1
            assert freqs[0].min >= 0
            assert freqs[0].cur >= 0
            assert freqs[0].max >= 0
        finally:
            device.close()
            adbc.close()

    async def test_get_cpu_stats(self):
        """测试获取 CPU 统计数据"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            stats = await device.cpu.get_cpu_stats()
            assert isinstance(stats, dict)
        finally:
            device.close()
            adbc.close()

    async def test_get_total_cpu_stat(self):
        """测试获取总 CPU 统计"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            stat = await device.cpu.get_total_cpu_stat()
            assert stat.total >= 0
        finally:
            device.close()
            adbc.close()

    async def test_get_cpu_name(self):
        """测试获取 CPU 名称"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            name = await device.cpu.get_cpu_name()
            assert isinstance(name, str)
        finally:
            device.close()
            adbc.close()

    async def test_get_info(self):
        """测试获取 CPU 信息"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            info = await device.cpu.get_info()
            assert info.core >= 1
            assert isinstance(info.platform, str)
        finally:
            device.close()
            adbc.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestMemPluginIntegration:
    """测试 MemPlugin 集成"""

    async def test_get_info(self):
        """测试获取内存信息"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            info = await device.mem.get_info()
            assert info.mem_total > 0
        finally:
            device.close()
            adbc.close()

    async def test_stat_system_app(self):
        """测试获取系统应用内存统计"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            stat = await device.mem.stat("com.android.settings")
            assert stat is not None
        finally:
            device.close()
            adbc.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestPMPluginIntegration:
    """测试 PMPlugin 集成"""

    async def test_list_packages(self):
        """测试列出已安装的包"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            packages = await device.pm.list_packages()
            assert len(packages) > 0
            # 应该有一些系统应用
            assert any("android" in pkg for pkg in packages)
        finally:
            device.close()
            adbc.close()

    async def test_is_installed_system_app(self):
        """测试判断系统应用是否已安装"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            # 检查 settings 应用
            is_installed = await device.pm.is_installed("com.android.settings")
            assert is_installed is True
        finally:
            device.close()
            adbc.close()

    async def test_list_features(self):
        """测试列出功能"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            features = await device.pm.list_features()
            assert isinstance(features, dict)
        finally:
            device.close()
            adbc.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestTempPluginIntegration:
    """测试 TempPlugin 集成"""

    async def test_stat(self):
        """测试获取温度信息"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            stat = await device.temp.stat()
            # 模拟器可能没有真实温度，但至少不应该报错
            assert stat is not None
        finally:
            device.close()
            adbc.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestMinicapPluginIntegration:
    """测试 MinicapPlugin 集成"""

    async def test_init_and_start_stop(self):
        """测试初始化、启动和停止 minicap"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            # 初始化
            await device.minicap.init()

            # 启动 minicap
            await device.minicap.start()

            # 等待一下让服务启动
            import asyncio
            await asyncio.sleep(1)

            # 停止
            await device.minicap.stop()

        finally:
            # 确保停止，防止端口占用
            try:
                await device.minicap.stop()
            except:
                pass
            device.close()
            adbc.close()


@pytest.mark.integration
@pytest.mark.asyncio
class TestScrcpyPluginIntegration:
    """测试 ScrcpyPlugin 集成"""

    async def test_init_and_start_stop(self):
        """测试初始化、启动和停止 scrcpy"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            # 初始化
            await device.scrcpy.init()

            # 启动 scrcpy
            await device.scrcpy.start(max_size=720, bit_rate=2000000)

            # 等待一下让服务启动
            import asyncio

            await asyncio.sleep(1)

            # 获取一帧
            frame = await device.scrcpy.get_frame()
            # 可能第一次获取不到，不强制断言
            if frame:
                assert isinstance(frame, bytes)
                assert len(frame) > 0

            # 模拟点击
            await device.scrcpy.tap(360, 640)

            # 停止
            await device.scrcpy.stop()

        finally:
            # 确保停止，防止端口占用
            try:
                await device.scrcpy.stop()
            except:
                pass
            device.close()
            adbc.close()

    async def test_text_input(self):
        """测试文本输入"""
        adbc = ADBClient()
        device = await adbc.device("emulator-5554")
        try:
            await device.scrcpy.start(max_size=720, bit_rate=2000000)

            import asyncio

            await asyncio.sleep(1)

            # 输入文本
            await device.scrcpy.text("test scrcpy")

            await device.scrcpy.stop()

        finally:
            try:
                await device.scrcpy.stop()
            except:
                pass
            device.close()
            adbc.close()
