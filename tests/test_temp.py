from unittest.async_case import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock,MagicMock
from async_adbc.device import Device
from async_adbc.device import TempPlugin

class TestTemp(IsolatedAsyncioTestCase):
    
    async def test_stat(self):
        # mock一个Device,让其异步方法 shell 返回"helloword"
        device = MagicMock(spec=Device)
        dump_value = """
        ****** Dump of HardwarePropertiesManagerService ******
        CPU temperatures: [31.4, 31.8, 31.4, 31.4, 32.7, 31.9, 31.4, 31.9]
        CPU throttling temperatures: [95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]
        CPU shutdown temperatures: [115.0, 115.0, 115.0, 115.0, 115.0, 115.0, 115.0, 115.0]
        CPU vr throttling temperatures: [95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]
        GPU temperatures: [30.7, 30.7, 30.7, 31.5, 31.1, 30.7, 30.3, 30.7]
        GPU throttling temperatures: [95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]
        GPU shutdown temperatures: [115.0, 115.0, 115.0, 115.0, 115.0, 115.0, 115.0, 115.0]
        GPU vr throttling temperatures: [95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]
        Battery temperatures: [29.1]
        Battery throttling temperatures: [80.0]
        Battery shutdown temperatures: [90.0]
        Battery vr throttling temperatures: [80.0]
        Skin temperatures: [30.459]
        Skin throttling temperatures: [46.5]
        Skin shutdown temperatures: [95.0]
        Skin vr throttling temperatures: [46.5]
        Fan speed: []

        Cpu usage of core: 0, active = 984100, total = 3727757
        Cpu usage of core: 1, active = 791709, total = 3873520
        Cpu usage of core: 2, active = 789328, total = 3865533
        Cpu usage of core: 3, active = 564362, total = 4012228
        Cpu usage of core: 4, active = 418064, total = 4043632
        Cpu usage of core: 5, active = 311618, total = 4059520
        Cpu usage of core: 6, active = 303790, total = 4059706
        Cpu usage of core: 7, active = 203052, total = 4071083
        ****** End of HardwarePropertiesManagerService dump ******
        
        """
        device.shell = AsyncMock(return_value=dump_value)
        # ret = await device.shell()

        temp_plugin = TempPlugin(device)
        
        stat = await temp_plugin.stat()
        
        self.assertEqual(stat.cpu, 31.4)
        self.assertGreaterEqual(stat.gpu, 30.7)
        self.assertGreaterEqual(stat.skin,30.459)
        self.assertGreaterEqual(stat.battery, 29.1)
        
        
        device.shell = AsyncMock(return_value="")

        stat = await temp_plugin.stat()

        self.assertEqual(stat.cpu, 0)
        self.assertGreaterEqual(stat.gpu, 0)
        self.assertGreaterEqual(stat.skin,0)
        self.assertGreaterEqual(stat.battery, 0)
