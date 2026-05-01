# 重构文档

本目录包含 async-adbc v2.0 重构相关的所有文档。

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [v2.0-plan.md](./v2.0-plan.md) | **重构方案主文档** - 详细的重构计划和实施方案 |
| [issues.md](./issues.md) | **问题清单** - 代码库中发现的具体问题列表 |
| [../architecture/overview.md](../architecture/overview.md) | **架构概览** - 系统架构设计说明 |

## 🎯 快速导航

### 想了解重构的整体计划？
→ 阅读 [v2.0-plan.md](./v2.0-plan.md)

### 想查看发现的具体问题？
→ 查看 [issues.md](./issues.md)

### 想了解系统架构？
→ 阅读 [architecture/overview.md](../architecture/overview.md)

## 📋 重构摘要

### 目标架构
```
async_adbc/
├── config.py              # 配置常量
├── exceptions.py          # 所有异常
├── models.py              # 所有数据模型
├── plugin.py              # Plugin基类 + 注册表
├── protocol/              # 拆分后的协议模块
│   ├── consts.py
│   ├── connection.py
│   └── response.py
├── service/
│   ├── base.py
│   ├── host.py
│   └── local.py
└── plugins/               # 自动注册的插件
    └── _registry.py
```

### 主要改进
1. ✅ 插件自动注册机制
2. ✅ 统一的异常和模型管理
3. ✅ 更清晰的模块职责
4. ✅ 消除循环依赖
5. ✅ 更好的可扩展性

## 🔗 相关资源

- [项目 README](../../README.md)
- [adb 协议文档](https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md)
