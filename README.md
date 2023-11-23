# ADBC

[![Test-测试](https://github.com/kaluluosi/async-adbc/actions/workflows/test.yml/badge.svg)](https://github.com/kaluluosi/async-adbc/actions/workflows/test.yml)


ADBC是ADB Client的纯python异步实现，ADBC直接跟ADB Server通信不需要靠进程调用命令行来执行ADB命令。
有以下特性：
1. 支持async/await和同步调用
2. 封装了一些性能测试相关的方法，供性能采集工具使用
3. 以`service（服务）`为单位封装命令方法，能够跟 `adb`和`android shell`命令更加一致。


## 安装

```shell
pip install async-adbc
```
## 快速入门

### 使用`ADBClient`
`ADBClient`对应的是`adb`命令

>**note**
>当连接设备只有一个的时候，`adb`命令可以省略`-s <serialno>`，但是`ADBClient`不会包含这种默认设备的命令方法。因为`async-adbc`认为`adb`和`device`应该职责分明不应有太多的潜规则。因此用户想要操作某个设备一定要使用`Device`对象下的方法，`Device`下的方法相当于是帮我们默认传递了`-s <serialno>`。

```python
from async_adbc import ADBClient

adbc = ADBClient() # 默认连接 127.0.0.1:5037 ，也就是本机的adb server
version = awaitadbc.version() # 对应 `adb version`
print(version)

# 获取Android设备对象，对应 `adb devices`
devices = adbc.devices()
for device in devices:
    print(device.serialno)
```

### 使用`Device`
`Device`对象是对Android设备的抽象，所有需要指定 `-s <serialno>` 的操作都被封装到 `Device` 类中。

```python
from async_adbc import ADBClient

adbc = ADBClient()

# 获取Android设备对象，对应 `adb devices`
default_device = adbc.device() # 获取 `adb devices` 的第一个设备

product_model = await defualt_device.prop.get("ro.product.model")
print(product_model)

# `device.pm` 对应 `adb shell pm`
packages = await default_device.pm.list_packages()
print(packages)

# `device.shell` 对应 `adb shell`
ret = await default_device.shell("echo hello")
print(ret)

# 封装了 `fps` ，用来获取安卓游戏的帧率，方案参考了`solopi`
fps_stat = await default_device.fps.stat("PKG_NAME")
print(fps_stat)

# 封装了 `mem`，用来获取安卓设备的内存信息
mem_stat = await default_device.mem.stat("PKB_NAME")
print(mem_stat)

# 还有流量、温度等等工具的封装...
```


## 参考
1. adb协议 https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md
2. ppadb https://github.com/Swind/pure-python-adb
