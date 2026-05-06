# scrcpy 手动测试指南

## 快速操作步骤

### 1. 连接设备
```bash
# 连接你的设备
adb connect 127.0.0.1:5555

# 确认设备已连接
adb devices
```

### 2. 推送 scrcpy-server.jar 到设备（如果还没有）
```bash
# 推送 jar 包
adb push C:/Users/kalul/Documents/GitHub/async-adbc/async_adbc/vendor/scrcpy/scrcpy-server.jar /data/local/tmp/

# 设置权限
adb shell chmod 644 /data/local/tmp/scrcpy-server.jar

# 确认文件已推送
adb shell ls -lh /data/local/tmp/scrcpy-server.jar
```

### 3. 查看设备信息
```bash
# Android 版本
adb shell getprop ro.build.version.release

# API 级别
adb shell getprop ro.build.version.sdk

# CPU 架构
adb shell getprop ro.product.cpu.abi

# 设备特性（是否是模拟器）
adb shell getprop ro.build.characteristics
```

### 4. 设置端口转发
```bash
# 设置端口转发：本地 27183 -> 设备的 scrcpy socket
adb forward tcp:27183 localabstract:scrcpy
```

### 5. 启动 scrcpy 服务器（在一个新的终端窗口）

打开一个新的命令提示符窗口，执行：
```bash
adb shell "export CLASSPATH=/data/local/tmp/scrcpy-server.jar && app_process / com.genymobile.scrcpy.Server log_level=debug bit_rate=2000000"
```

这个命令会：
- 启动 scrcpy 服务器
- 使用 debug 日志级别
- 设置比特率为 2Mbps
- 服务器会保持运行，直到你按 Ctrl+C

**注意**：
- `app_process /` 表示在工作目录 / 下执行
- `com.genymobile.scrcpy.Server` 是完整的 Java 类名（不是 `scrcpy.Server`）

### 6. 测试连接（在原来的终端窗口）

等待 2-3 秒让服务器启动，然后测试连接：
```bash
# 使用 PowerShell 测试连接
powershell -Command "$client = New-Object System.Net.Sockets.TcpClient; try { $client.Connect('127.0.0.1', 27183); Write-Host '连接成功'; $client.Close() } catch { Write-Host '连接失败: ' $_.Exception.Message }"
```

或者使用 `netcat`（如果已安装）：
```bash
nc -zv 127.0.0.1 27183
```

### 7. 清理
```bash
# 移除端口转发
adb forward --remove tcp:27183

# 在服务器窗口按 Ctrl+C 停止服务器
```

## 可能的结果

### 情况 1: 服务器正常启动
- 服务器窗口保持运行，没有错误信息
- 连接测试显示"连接成功"
- 可以继续测试数据流

### 情况 2: 服务器立即崩溃
- 服务器窗口显示 "Aborted" 或其他错误
- 连接测试显示"连接失败"
- 可能是设备兼容性问题

### 情况 3: 服务器启动但连接失败
- 服务器窗口显示启动成功
- 但连接测试显示"连接失败"
- 可能是端口转发或网络问题

## 完整的一键测试脚本

我已经创建了两个自动测试脚本：

### Linux/Mac:
```bash
bash test_scrcpy_manual.sh
```

### Windows:
```cmd
test_scrcpy_manual.bat
```

这些脚本会自动完成所有步骤，包括推送文件、设置端口转发、测试连接等。

## 调试建议

如果服务器崩溃，可以：
1. 增加 `log_level=verbose` 查看更详细的日志
2. 检查设备是否满足最低要求（API 21+）
3. 尝试不同的比特率参数
4. 查看系统日志：`adb logcat | grep scrcpy`