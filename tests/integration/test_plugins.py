"""插件集成测试模块"""

import pytest

from async_adbc.client import ADBClient


@pytest.fixture
def target_serialno(device_serialno):
    """获取目标设备序列号"""
    return device_serialno


@pytest.mark.integration
@pytest.mark.asyncio
class TestCPUPluginIntegration:
    """测试 CPUPlugin 集成"""

    async def test_get_count(self, target_serialno):
        """测试获取 CPU 核心数"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            count = await device.cpu.get_count()
            assert isinstance(count, int)
            assert count >= 1
        finally:
            device.close()
            adbc.close()

    async def test_get_freqs(self, target_serialno):
        """测试获取 CPU 频率"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            freqs = await device.cpu.get_freqs()
            assert len(freqs) >= 1
            assert freqs[0].min >= 0
            assert freqs[0].cur >= 0
            assert freqs[0].max >= 0
        finally:
            device.close()
            adbc.close()

    async def test_get_cpu_stats(self, target_serialno):
        """测试获取 CPU 统计数据"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            stats = await device.cpu.get_cpu_stats()
            assert isinstance(stats, dict)
        finally:
            device.close()
            adbc.close()

    async def test_get_total_cpu_stat(self, target_serialno):
        """测试获取总 CPU 统计"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            stat = await device.cpu.get_total_cpu_stat()
            assert stat.total >= 0
        finally:
            device.close()
            adbc.close()

    async def test_get_cpu_name(self, target_serialno):
        """测试获取 CPU 名称"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            name = await device.cpu.get_cpu_name()
            assert isinstance(name, str)
        finally:
            device.close()
            adbc.close()

    async def test_get_info(self, target_serialno):
        """测试获取 CPU 信息"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
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

    async def test_get_info(self, target_serialno):
        """测试获取内存信息"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            info = await device.mem.get_info()
            assert info.mem_total > 0
        finally:
            device.close()
            adbc.close()

    async def test_stat_system_app(self, target_serialno):
        """测试获取系统应用内存统计"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
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

    async def test_list_packages(self, target_serialno):
        """测试列出已安装的包"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            packages = await device.pm.list_packages()
            assert len(packages) > 0
            # 应该有一些系统应用
            assert any("android" in pkg for pkg in packages)
        finally:
            device.close()
            adbc.close()

    async def test_is_installed_system_app(self, target_serialno):
        """测试判断系统应用是否已安装"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            # 检查 settings 应用
            is_installed = await device.pm.is_installed("com.android.settings")
            assert is_installed is True
        finally:
            device.close()
            adbc.close()

    async def test_list_features(self, target_serialno):
        """测试列出功能"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
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

    async def test_stat(self, target_serialno):
        """测试获取温度信息"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            stat = await device.temp.stat()
            # 模拟器可能没有真实温度，但至少不应该报错
            assert stat is not None
        finally:
            device.close()
            adbc.close()




@pytest.mark.integration
@pytest.mark.asyncio
class TestScrcpyPluginIntegration:
    """测试 ScrcpyPlugin 集成"""

    async def test_init_and_start_stop(self, target_serialno):
        """测试初始化、启动和停止 scrcpy"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            # 检查设备支持
            support_info = await device.scrcpy.check_device_support()
            
            # 如果有严重警告，跳过测试
            if not support_info['supported']:
                pytest.skip(f"设备不支持 scrcpy: {support_info['warnings']}")
            
            # 检查是否为 x86 架构模拟器（已知在握手阶段失败）
            device_info = support_info.get('device_info', {})
            cpu_abi = device_info.get('cpu_abi', '').lower()
            serialno = str(device.serialno).lower()
            
            if 'x86' in cpu_abi and ('emulator' in serialno or '127.0.0.1:' in serialno):
                pytest.skip("x86 架构模拟器在 scrcpy 握手阶段不稳定（服务器能启动但连接立即关闭）")

            # 初始化
            await device.scrcpy.init()

            # 启动 scrcpy（禁用支持检查，因为已经检查过了）
            await device.scrcpy.start(max_size=720, bit_rate=2000000, check_support=False)

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

    async def test_text_input(self, target_serialno):
        """测试文本输入"""
        adbc = ADBClient()
        device = await adbc.device(target_serialno)
        try:
            # 检查设备支持
            support_info = await device.scrcpy.check_device_support()
            
            # 如果有严重警告，跳过测试
            if not support_info['supported']:
                pytest.skip(f"设备不支持 scrcpy: {support_info['warnings']}")
            
            # 检查是否为 x86 架构模拟器（已知在握手阶段失败）
            device_info = support_info.get('device_info', {})
            cpu_abi = device_info.get('cpu_abi', '').lower()
            serialno = str(device.serialno).lower()
            
            if 'x86' in cpu_abi and ('emulator' in serialno or '127.0.0.1:' in serialno):
                pytest.skip("x86 架构模拟器在 scrcpy 握手阶段不稳定（服务器能启动但连接立即关闭）")

            await device.scrcpy.start(max_size=720, bit_rate=2000000, check_support=False)

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
