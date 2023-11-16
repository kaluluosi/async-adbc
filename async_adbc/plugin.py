'''
author:        kaluluosi111 <kaluluosi@gmail.com>
date:          2023-11-17 01:58:11
Copyright © YourCompanyName All rights reserved
'''
import typing
if typing.TYPE_CHECKING:
    from async_adbc.device import Device

class Plugin:
    def __init__(self, device: "Device"):
        self._device = device
