from asyncio import run
import time
from async_adbc import ADBClient
from ppadb.client import Client
from ppadb.device import Device

adbc = ADBClient()

dev = run(adbc.device())




while True:
    total_cpu_usage = run(dev.cpu.total_cpu_usage)
    app_cpu_usage = run(dev.cpu.get_pid_cpu_usage("com.test.ddxe_0524"))
    # print(total_cpu_usage)
    print(app_cpu_usage)
    time.sleep(1)

# adbc = Client()
# dev:Device = adbc.devices()[0]

# while True:
#     # start = dev.cpu_times()
#     # print("start",start)
#     # end = dev.cpu_times()
#     # print("end  ",end)

#     # diff = end - start
#     # print("usage", (diff.user+diff.system)/diff.total()*100)
#     print("cpu percent",dev.cpu_percent())