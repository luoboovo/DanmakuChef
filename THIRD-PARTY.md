# 第三方来源

参考项目：https://github.com/luoboovo/radish-danmaku-eat

参考接口：feeding_game/bili_listener.py（blivedm 监听、交易 ID 去重）与 feeding_game/gift_catalog.py（roomGiftList）。本项目桥接是独立实现，没有引入 PyQt 游戏代码。

附带的 blivedm 1.1.7 wheel 来自该仓库 vendor/blivedm-1.1.7-py3-none-any.whl，原始许可证保留在 bridge/BLIVEDM-LICENSE.txt，也保留于 wheel 内。它提供 SEND_GIFT / SEND_GIFT_V2、DANMU_MSG 模型以及 face 头像字段。aiohttp、Brotli、pure-protobuf、yarl 等安装依赖遵循各自许可证。

所有厨房与角色占位美术由本项目 Canvas 代码绘制；B 站头像、礼物图片 URL 是平台事件资源。
