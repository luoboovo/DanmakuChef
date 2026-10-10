# 主播拌面店 · B 站礼物互动原型

## Windows 离线试玩

解压整个项目，用 Edge / Chrome 双击 `web/index.html`，无需安装、联网或购买素材。也可以在 PowerShell 7 执行 `pwsh -File ./Start-Offline.ps1`。

1. 点击「模拟礼物点餐」，顾客进入队伍。
2. 按住碗架拖出空碗，松开摆到浅色工作台。
3. 按住锅拖出面条，或按住保温盒拖出臊子，松开到碗中。
4. 食材可先放台面，再次拖进碗；不限添加顺序和份数。
5. 拖动整只碗，食材数据保持。碗不能重叠；无效位置恢复原位，新碗返回架子。
6. 碗显示「可出餐」后，仍能加料。选中碗，点击「试验出餐」手动交付给队首顾客。
7. 顾客超过七位，用「下一组顾客」翻页。没有金币、计时、惩罚或自动出餐。

## Windows 真实 B 站接入

安装 Python 3.12 与 PowerShell 7。在项目目录执行：

```powershell
pwsh -File ./Start-Live.ps1 -Room 你的房间号 -Login
```

`-Room` 后替换为数字；如不需要登录，可去掉 `-Login`。第一次执行安装桥接依赖，需要网络。输入 SESSDATA 时终端隐藏输入，Cookie 仅存于当前 Python 进程，不写文件。停止进程后清除。不要把 Cookie 放入网页、截图或提交源码。

打开 `http://127.0.0.1:8765`，点「直播接入」，设置礼物名称或 ID，再点「连接桥接」。浏览器连接本地桥接不代表已经连接 B 站；状态栏在真正的 B 站 WebSocket 连接成功后才显示「B 站已连接」。断网由 blivedm 重连；监听停止需重启桥接。

直播模式请使用上面的本地 HTTP 地址，双击打开的离线页面不用于连接桥接。桥接仅监听本机回环地址，并校验浏览器 Origin。

默认小心心触发订单。礼物 ID 配置优先于名称；名称必须与事件一致。每条礼物事件默认生成一位顾客，界面可以改为每个礼物一位。连送只按交易 ID 去重，不按观众冷却。缺少交易 ID 的事件不擅自去重。弹幕只展示，并可按 UID 更新队伍头像，不触发点餐。

`http://127.0.0.1:8765/catalog` 返回配置房间的礼物 ID、名称和图标 URL，采用参考项目的 roomGiftList 接口；获取失败返回 502，不影响离线制作。顾客头像直接读取 blivedm 礼物 / 弹幕模型的 face；头像缺失或加载失败显示内置 Q 版角色。基础美术全部使用本地 Canvas 绘制，不依赖网络。头像本身属于在线资源。

## 文件结构

```text
web/
  index.html       游戏入口
  style.css        网页界面
  config.js        礼物规则、工作台、临时配置
  systems.js       状态、配方、碰撞、拖拽、礼物适配、顾客订单
  renderer.js      可独立替换的 Canvas 美术与渲染
  game.js          Pointer 输入、界面、WebSocket 接入、主循环
bridge/
  server.py       B 站监听、本地网页服务、WebSocket、礼物目录
  requirements.txt
  blivedm-1.1.7-py3-none-any.whl
  BLIVEDM-LICENSE.txt
tests/
  core.test.cjs    核心逻辑回归
  bridge_smoke.py  本地桥接验证
Start-Offline.ps1
Start-Live.ps1
README.md
THIRD-PARTY.md
```

## 临时机制与扩展入口

- 出餐机制尚未确认：`GameState.deliver()` 采用选中碗 + 手动按钮 + FIFO 的演示方式，不自动交付，不要求精确份数。可整体替换此接口。
- 每条 / 每个礼物的订单映射属于临时可配置选择，见 `config.js` 的 quantityMode。
- 无效摆碗集中在 `CollisionSystem.valid()` 与 `DragSystem.up()`；食材边界集中在 Workbench.clamp()。
- 可出餐条件集中在 RecipeSystem.ready()。
- 所有事件经 GiftEventAdapter.receive()，模拟与 B 站共用入口。事件包含 type、uid、name、avatar、giftId、giftName、quantity、transactionId、source。
- 每个碗独立记录 noodles 与 sauce。渲染使用分布式面线与肉粒，多次加料视觉逐步增加；极大数量显示量封顶，实际计数不封顶。
- 刷新页面会重置本次游戏。第一阶段没有持久化或未确认的经济系统。

## 验证

已通过 Node 核心回归：自由放置与重新拾取、任意顺序重复加料、碗数据独立、移动保持数量、碰撞回退、新碗拒绝重叠、食材边界、取消拖拽、礼物交易去重、连送模式、FIFO 手动交付。Python 桥接启动、网页服务、WebSocket 初始状态已通过。JS / Python 语法检查通过。

```powershell
node ./tests/core.test.cjs
./.venv/Scripts/python.exe ./tests/bridge_smoke.py
```

当前执行环境禁止访问 B 站域名，所以真实房间、登录、礼物目录和在线头像未做端到端验证。浏览器画面与 Windows 脚本未在此环境进行人工实测。请在自己的房间用一次真实礼物验证；接口变化、B 站风控或房间权限可导致连接失败，不能把本地模拟成功当成真实连接成功。
