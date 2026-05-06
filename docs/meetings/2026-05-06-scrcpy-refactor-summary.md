# Scrcpy 插件重构开发总结
日期：2026-05-06
参会人员：煊哥、Claude

---

## 一、本次完成的工作

### 1.1 项目清理
- 删除 minicap 相关代码和文件完全移除
- 清理旧的 scrcpy 残留

### 1.2 Scrcpy 插件重写
- 基于 scrcpy-server v3.3.4
- 正确实现 `adb reverse` 端口转发 + `shell_reader` 启动服务
- 实现完整的握手协议

### 1.3 核心功能
- `start() / stop()
- `stream_frames()` 异步生成器
- `screencap(save_file)` 支持直接保存 png/jpg/h264
- `record()` 录制视频

### 1.4 项目规范
- 使用 `uv add --optional scrcpy av pillow` 添加依赖

---

## 二、踩过的坑和心得

### 坑点 1：adb forward vs adb reverse
**问题描述**：最开始搞反了！

**现象**：
- `adb forward`：是主机端口 -> 设备（主机主动连
- `adb reverse`：是设备端口 -> 主机（设备主动连主机

**解决**：scrcpy-server 是运行在设备上主动连主机，所以必须用 `reverse`

**心得**：
- 先理解通信方向，再选 forward/reverse
- 不要凭感觉！

---

### 坑点 2：握手协议必须收满数据
**问题描述**：用简单的 `sock.recv()` 不一定能收满期望字节数，导致握手解析错乱

**现象**：
- 设备名读到的 width/height 是完全离谱的数值（比如 842413056）
- 因为收到的数据错位，解析出来分辨率完全不对

**原因**：TCP 是流协议，`recv(n)` 只保证 >0，不保证 ==n

**解决**：实现 `_recv_exact()` 循环读取直到收满

**心得**：
- socket 编程基础不能偷懒！
- 所有协议数据必须用 `_recv_exact` 类似函数

---

### 坑点 3：手协议读到分辨率不可信，用 wm.size() 兜底
**问题描述**：握手读到的 width/height 在 Bluestacks 5 等模拟器上完全不对

**现象**：width_bytes 里存的是 "264" 的 ASCII 码而不是真正的分辨率

**解决**：握手后调用 `device.wm.size()` 拿到真实分辨率覆盖

**心得**：
- 不要完全相信单一数据源
- 有疑问就交叉验证

---

### 坑点 4：H.264 数据太少解码失败/绿屏
**问题描述**：screencap 收得太快导致：
1. 没有 SPS/PPS 头
2. 没有关键帧
3. 数据从流中间截出来的

**现象**：
- 绿屏（只有一半画面）
- PyAV 直接报错 `Invalid data found when processing input`

**原因**：
- H.264 需要 SPS/PPS + 关键帧才能完整解码
- 只收几十 KB 可能只收到切片数据

**解决**：
1. `min_duration=0.5s` 至少收 0.5 秒
2. `min_size=80KB` 至少收 80KB
3. `keyframe_interval=10` 让 scrcpy-server 多发关键帧

**心得**：
- 视频编码不是想截就能截！
- 要有耐心，收够数据

---

### 坑点 5：PyAV 解码方式
**问题描述**：
- `av.open(bytes(buffer))` ❌ 不支持直接传 bytes
- `av.open(BytesIO(buffer))` ✅ 可以但有时不稳定
- 写临时文件再打开 ❌ 但是最稳定

**解决**：最终用回 `BytesIO`，配合收够数据，效果不错

**心得**：
- 读库文档/试试就知道了
- 可以试几种方案选最稳妥的

---

### 坑点 6：项目规范！uv vs pip
**问题描述**：用 `pip install av pillow` 安装，pyproject.toml 没记录！

**解决**：用 `uv add --optional scrcpy av pillow`

**心得**：
- **项目规范**，用 uv/pipenv/poetry 等工具管理！
- 不要手动 pip install

---

## 三、经验总结

### 3.1 开发方法论
1. **预演先行**：先写简单独立脚本验证核心逻辑
2. **最小可用**：先跑通最基本流程，再优化
3. **边试边调**：有问题现场打印，不要靠猜
4. **对比验证**：拿工作的版本对照调试版本

### 3.2 技术要点
1. **socket 协议必须用 `_recv_exact`
2. **H.264** 需要完整头+关键帧才能解码
3. **adb reverse/forward** 搞清楚连接方向
4. **WMPlugin 是个好东西，分辨率等可以兜底

### 3.3 Scrcpy 工作原理回顾
```
主机：监听端口
设备：scrcpy-server 启动 -> reverse -> 连主机
握手：dummy(1) + name(64) + width(4BE) + height(4BE)
流：H.264 NALUs
```

---

## 四、验收结果
- ✅ 分辨率正确：1920x1080
- ✅ 截图完整无绿屏
- ✅ 接口易用：`screencap("test.png")` 直接保存
- ✅ 项目规范：依赖记录在 pyproject.toml [scrcpy] optional 组
