# async-adbc 项目备忘录

## 基本信息
- 项目名称：async-adbc - 纯 Python 异步 ADB Client 库
- 项目路径：C:\Users\kalul\Documents\GitHub\async-adbc
- 当前版本：2.0.0
- 用户：煊哥（项目维护者 kaluluosi）

## 用户偏好
- 喜欢详细规划，文档先行
- 喜欢分阶段迭代，小步提交
- 重视向后兼容性
- 重视代码质量和文档
- 喜欢现代工具链（uv, pytest）

## v2.0 重构关键决策
- 包管理：poetry → uv
- 测试框架：unittest → pytest + 分层 mock
- 插件系统：注册表 + 装饰器 + 自动发现
- 连接管理：从共享连接改回每次请求独立连接（避免流式读取冲突）
- API 风格：统一 async 方法，移除 async property
- 兼容性：多层降级 + check=False 参数

## 当前开发计划（2.2.0）
1. 删除 minicap 相关代码（未正式发布，模拟器支持差）
2. 完善 ScrcpyPlugin：
   - 新增 screencap() 方法
   - 新增 stream_frames() 异步生成器
   - 新增 record() 录像方法
   - 完善测试用例
3. 更新文档和版本号

## CLAUDE.md 原则
- 先思考再编码
- 简单优先
- 精准改动
- 目标驱动执行

## 历史版本
- 2.0.0：2026-05-01 完成 v1.x → v2.0 大型重构
