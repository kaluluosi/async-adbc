# ADBC

ADBC是ADB Client的纯python异步实现，ADBC直接跟ADB Server通信不需要靠进程调用命令行来执行ADB命令。
有以下特性：
1. 支持async/await和同步调用
2. 封装了一些性能测试有用的接口，供性能采集工具使用

## 参考
1. adb协议 https://github.com/kaluluosi/adbDocumentation/blob/master/README.zh-cn.md
2. ppadb https://github.com/Swind/pure-python-adb