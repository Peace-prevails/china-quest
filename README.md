# China Quest

北京都市荒诞悬疑 × 零基础中文。EP01《一碗牛肉面，十亿遗产》。

当前交付包含可本地运行的手机浏览器第一集试玩版、结构化故事与 Seedream 图片生产／审核流水线。Python 3.11+ 标准库启动，浏览器无需安装依赖；开发检验另需 Node.js 22+。

## 浏览器试玩

```sh
python3 scripts/serve_game.py
```

打开 http://127.0.0.1:8767 。完整覆盖 S0–S9、菜单点单、动态账单、五个探索热点、正式 CG、短信结尾与独立探索回放。每次选择保存到当前浏览器 localStorage；结尾可下载 JSON 存档。英文任务始终显示，翻译和拼音可切换，每个新场景默认展开。

`web/` 是无需打包依赖的前端源文件。`scripts/build_web.py` 校验12项原批准图与修订预览图哈希，将前端、故事及批准图复制到 `local/web/`；服务器只公开此目录，不公开整个仓库。当前入口仅限本机；手机尺寸已在浏览器检验，尚未部署公网。

本版为文字与拼音试玩：人物随说话对象切换实景镜头，并按剧情切换友善、迟疑、凝重等静态表情；语音、透明立绘尚未制作。牛肉面／炸酱面有各自的上菜镜头，菜单中炸酱面和可乐仍用UI图标。拼音采用教学用读音提示（含一／不变调），后续录音前仍需逐句校音。

```sh
python3 -m unittest discover -s tests -p test_web.py -v
```

新增双语剧情衔接：玩家抵京找饭、进店落座、上菜、小陈身份、顾承泽携文件进店、第二人打断、老板娘看文件、收到短信。衔接旁白不随语言提示隐藏；原始批准图不变，`visual_revision.json` 中16项修订为待用户审阅的试玩版本。

包含128条网页/Python剧情对照路线、存档恢复、回放隔离、全部选项及动态台词拼音覆盖与公开素材包检查。

## 本地验收

```sh
python3 scripts/validate_story.py
python3 -m unittest discover -s tests -v
python3 scripts/story.py
python3 scripts/generate_assets.py --dry-run --asset-id CH01_OWNER --max-images 1
python3 scripts/review_assets.py
```

终端试玩包含菜单卡、点餐取消／帮助、动态账单、五个可重玩热点、S6–S9 收束与结尾状态保存。探索没有强制计时，不要求完成全部热点，选择“继续吃面”即可退出。S6 后不再返回探索。中英文及浏览器拼音已提供；动态台词通过 web/pinyin.json 匹配，语音配置已预留，本阶段不调用 TTS。

## 单张付费测试（需要人工批准张数和费用）

1. `cp .env.example .env`，在本地填写 Key 和控制台实际可用模型 ID。不要提交 .env 或原始凭据文件。
2. 根据控制台当期计价确认单张费用，再 dry-run。model 不预填臆造的 flash/pro 名字。
3. 只有获得用户对张数与费用的明确批准后执行以下命令，将 MODEL、PRICE、CAP 替换为真实值：

```sh
python3 scripts/generate_assets.py --asset-id CH01_OWNER --model MODEL --max-images 1 --unit-price-rmb PRICE --max-spend-rmb CAP --confirm-paid
```

`--unit-price-rmb` 是人工确认的单张费用上限，不是程序自动估价。每轮最大张数×单价必须小于预算。多轮调用需人工累计预算。用户已批准累计40元图片预算，已生成素材的估计与预留记录见 data/production_budget.json。

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

## 阶段验收与存档

```sh
python3 scripts/checkpoint.py stage-02
# 写入 docs/checkpoints/stage-02.json，标签不可覆盖；包含校验、测试、12 项 dry-run 输出
python3 scripts/story.py --resume
python3 scripts/story.py --replay-exploration
```

终端试玩每次选择自动存档，输入 `q` 保存退出。完成后可直接回放 S5 探索；回放另存 episode_01_replay.json，不覆盖给 EP02 的主线结尾。校验器遍历所有可达剧情状态并验证每个状态能结束，资产引用必须形成无环依赖图。GitHub Actions 在 Python 3.11 和 3.14 上运行离线验收，不使用 API Key。

```sh
python3 scripts/asset_status.py
python3 scripts/asset_status.py --output local/asset-status.json
# 仅在全部 12 项通过人工审核后才允许导出：
python3 scripts/asset_status.py --export-approved local/approved-manifest.json
```

当前阶段与未完成项见 [docs/PROGRESS.md](docs/PROGRESS.md)。离线 HTTP 集成测试会临时监听 127.0.0.1，需要运行环境允许本机端口；不调用外部图片服务。

诊断补充：HTTP 错误现在保存为脱敏的 http_error 字段。`request_rejected` 表示接口明确拒绝请求，修复原因后用新 candidate 标签留下重试记录；超时或 5xx 继续记为 uncertain 并禁止自动重发。`ModelNotOpen` 需要先在火山方舟控制台“开通管理”开通目标模型，Key 有效和模型目录中存在该 ID 都不能替代开通。

## 人物参考范围与累计预算

审批人物时默认只锁人物身份（identity_only），不把人物照片里的背景当作场景。可显式指定：

```sh
python3 scripts/review_assets.py --record PATH_TO_RECORD --decision approved --scope identity_only --note '只参考人物，不参考背景'
```

后续请求会附上每张参考图的用途说明；人物参考禁止用于定义背景资产。场景批准图使用 scene_layout，道具使用 object_only。老板娘 contour-v3 已由用户批准，仅人物；批准图和范围记录保存在 assets/approved/ 并进入 Git。

累计预算写入 data/production_budget.json，以请求 fingerprint 去重，成功、下载失败、超时等请求均保守占用预算，明确拒绝的请求不占用。删除本地生成图不会抹掉已存预算条目。数字为按公开单价的估计及预留，不是供应商账单。

```sh
python3 scripts/generate_candidate_batch.py              # 12 张选角候选 dry-run
# 仅在用户批准预算与继续制作后运行：
python3 scripts/generate_candidate_batch.py --execute    # 逐张执行；中断后可重复同命令，缓存命中不重发
python3 scripts/build_candidate_gallery.py
```

生图连接如遇本机 urllib TLS 中断，可在同样的审批和累计预算限制下使用 `ARK_HTTP_TRANSPORT=curl`。Key 通过临时权限文件传入，不出现在进程参数中；网络错误仍保守记录为 uncertain，不做自动付费重试。人工决定新尝试时必须保留旧请求预留并使用可审计的新 candidate 标签。

现代胡同资料与设计边界见 [docs/hutong_2026_reference_notes.md](docs/hutong_2026_reference_notes.md)。12项基础图片均已获得用户批准，正式清单为 episodes/ep01/approved_asset_manifest.json。

## 本集表达总结与配音调研

结尾新增9组表达复习卡：地点、点餐、拒绝、价格、听不懂、这个／那个、身份、认识关系。区分见过的表达与实际选择，给出拼音、意思和替换用法；新存档记录所选表达，旧存档不伪造选择记录，探索回放不污染主存档。

探索总景按订单切换，完整显示面碗、小陈擦桌、老板娘整理瓷碗与门外汽车；原有18项修订图仍为用户待审阅的预览版本。

现有方舟Key查询138项模型未见独立TTS；豆包语音服务与北京口音候选、鉴权区别、样音计划详见 [配音调研](docs/TTS_RESEARCH.md)。已用用户提供的 Seed-Audio 1.0 接口生成并选定角色样音；教学旁白按用户最新要求使用北京年轻女声。费用、鉴权实测与历史记录见同一文档。


## 第一集配音预览

对白、玩家选项和结尾9组表达支持本地MP3播放。点 `Listen` 试听选项不会提交选择；`Auto voice` 默认关闭，开启后朗读新节点；换节点、回标题、切到后台会停止旧音频。实际订单的两种面条和四种总价分别匹配，不用相似样音替代。音频暂不可用时仍可玩文字剧情。

```sh
python3 scripts/episode_audio.py           # 仅生成可审查清单，不调用API
python3 scripts/episode_audio.py --execute # 在已有预算授权内续跑；成功文件缓存，未决请求阻止重发
python3 scripts/build_web.py
node tests/audio_player.mjs
```

每批最多4个请求；预算锁串行更新，先按最长120秒预留每条2元，再按返回原始时长估算。只运行一个配音批处理进程，不与其他付费生成进程同时运行。`episodes/ep01/audio_manifest.json` 标记为 generated_preview：已选定声线方向，但生成模型不保证逐句音色完全相同，台词和口音仍需人工试听。发布包仅包含校验过的MP3，不包含密钥或供应商响应。

## 实物菜单与随手记

炸酱面和可乐已加入实物图预览，菜单、物品详情和订单缩略图复用统一图片映射。两张为额外素材，不更改原12张基础批准记录；提示词见episodes/ep01/menu_prop_plan.json。

游玩中可打开Notebook查看已发生情节及遇到的表达，避免提前透露遗产、第二个男人和短信。0.8倍慢速保持音高；自动朗读和语速偏好保存在独立偏好键，旧剧情存档兼容。打包为JS、CSS和数据请求附加内容版本号，避免浏览器缓存导致新素材丢失。阶段17通过43项测试与手机浏览器检查。
