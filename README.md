# China Quest

北京都市荒诞悬疑 × 零基础中文。EP01《一碗牛肉面，十亿遗产》。

当前交付是结构化故事与 Seedream 图片生产／审核流水线，不是完整手机游戏。Python 3.11+，仅使用标准库，无需安装依赖。

## 本地验收

```sh
python3 scripts/validate_story.py
python3 -m unittest discover -s tests -v
python3 scripts/story.py
python3 scripts/generate_assets.py --dry-run --asset-id CH01_OWNER --max-images 1
python3 scripts/review_assets.py
```

终端试玩包含菜单卡、点餐取消／帮助、动态账单、五个可重玩热点、S6–S9 收束与结尾状态保存。探索没有强制计时，不要求完成全部热点，选择“继续吃面”即可退出。S6 后不再返回探索。中英文已提供；pinyin 字段保留空值，尚待逐句校对，不宣称已交付中文语音／拼音教学体验。语音配置已预留，本阶段不调用 TTS。

## 单张付费测试（需要人工批准张数和费用）

1. `cp .env.example .env`，在本地填写 Key 和控制台实际可用模型 ID。不要提交 .env 或原始凭据文件。
2. 根据控制台当期计价确认单张费用，再 dry-run。model 不预填臆造的 flash/pro 名字。
3. 只有获得用户对张数与费用的明确批准后执行以下命令，将 MODEL、PRICE、CAP 替换为真实值：

```sh
python3 scripts/generate_assets.py --asset-id CH01_OWNER --model MODEL --max-images 1 --unit-price-rmb PRICE --max-spend-rmb CAP --confirm-paid
```

`--unit-price-rmb` 是人工确认的单张费用上限，不是程序自动估价。每轮最大张数×单价必须小于预算。多轮调用需人工累计预算。当前未授权任何付费生成。

每次 HTTP 请求仅生成一张；不发送新版 pro/flash 不支持的 sequential 参数。返回 URL 立即下载，记录响应、SHA256、提示词、模型、参考图哈希。生成 POST 超时／错误不自动重试，避免重复扣费；只有下载 GET 指数退避重试。状态 `uncertain` 必须先查供应商账单。下载失败可使用同命令 `--resume` 重用已保存响应，不重复 POST（链接过期需人工处理）。缓存命中校验文件哈希。候选通过 `--candidate 2` / `3` 区分；同候选重复运行必须 `--resume`。

## 人工审核与参考图锁定

```sh
python3 scripts/review_assets.py
# 浏览器打开 local/review/index.html
python3 scripts/review_assets.py --record assets/generated/characters/CH01_OWNER/CACHE_KEY/record.json --decision approved --note '身份、皮肤、手部通过；仍需透明抠图'
# 不合格用 --decision rejected，并记录原因
```

审核只接受已完整下载候选。批准时复制到按 SHA256 命名的不可变文件，并创建 reference.json；已有批准身份拒绝覆盖。后续 BG03/BG04 必须使用批准 BG02；CG 必须使用批准 BG02、顾承泽及文件袋。未批准参考图在 dry-run 中列为 blocked，真实请求前拒绝执行。依赖顺序：角色候选、BG02 候选 → 人工锁定 → 其余背景／道具 → CG。manifest 中 approved_reference_image 初始为 null，实际批准路径以 assets/approved/ID/reference.json 为唯一运行依据。生成图默认不提交 Git，避免大文件和临时签名 URL 泄露。

12 张是正式基础资产数，不是候选生成数。4 名角色各 3 候选 + BG02 的 3 候选 + 其余 7 张 = 首轮 22 张；不含重做／抠图，尚未批准费用。炸酱面与可乐使用 UI 图标，不额外消耗图片预算。角色图不能假定透明，需后续单独制作、审核透明立绘。

## 文件与后续工作

- docs/CODEX_BRIEF.md：完整原始交接说明；剧情真值。
- data/：第一季与角色设定；最终谜底未定，陆骁名称 provisional。
- episodes/ep01/：10 场景原文、可执行节点、菜单和 12 项资产提示词。
- scripts/：校验、试玩、生成和审核工具。

下一步：确认控制台模型与单张预算 → 只生成一张验证下载 → 人工审核 → 再决定候选批次。之后补齐拼音／教学语音和手机端 UI。暂不充值、不做视频、不自动批量调用。

接口依据：[火山方舟官方图片生成 API](https://console.volcengine.com/ark/region:cn-beijing/docs/image-generation-api)，核对于 2026-10-27。pro/flash、lite 等模型参数不同，尺寸／价格以实际模型控制台为准。
