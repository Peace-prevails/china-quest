# 北京口音配音调研 · 2026-10-30

## 当前账号配置核查

本地只有 ARK_API_KEY、ARK_IMAGE_MODEL（Seedream 5.0 Flash）和 HTTP 传输配置，没有单独的语音服务密钥。使用现有密钥只读 GET https://ark.cn-beijing.volces.com/api/v3/models，HTTP 200，返回138项；未发现独立 TTS 模型。包含音频相关能力描述的 Seed/Seedance 项不等于专门的文本转语音服务。模型目录不是账号所有已开通服务的完整权限证明。本次没有发送语音合成请求、没有产生配音费用，也没有证明现有方舟 Key 可用于豆包语音。

## 可采用的官方服务

- 豆包语音提供独立语音合成接口；新版使用 X-Api-Key，按 X-Api-Resource-Id 区分 seed-tts-1.0 / seed-tts-2.0。1.0与2.0的音色不能任意混用。
- 官方扣子系统音色列表列有“北京小爷”和“京腔侃爷”，均标为豆包语音合成1.0。扣子音色数字ID不是直接调用语音API的voice_type，接入前需在语音控制台确认对应标识。
- 方舟 Agent Plan 的语音服务文档另列 doubao-seed-tts-2.0，但明确需要专属API Key；不能据此认为当前图片API密钥已获得语音权限。

## 项目建议

先做3句短样音：“好嘞，面来了！”、“我是小陈，在这里帮忙。”、“终于找到你了！这个，是你的。”。比较轻北京口音、自然停顿、姓名与声调，不让夸张儿化影响初学者辨认。男性候选先试听北京小爷／京腔侃爷；女性角色另选适龄女声，不能把全员配成同一男声。

保留两条用途不同的音轨：NPC剧情用轻北京口音；学习总结用清晰普通话慢速跟读。逐句离线合成并缓存，前端只播放审核过的本地音频。按钮播放为默认，可选自动播放，换节点立即停止旧音频；同句/音色/参数按哈希缓存。动态价格和订单须分别生成，旁白与人物台词分开，不把动作说明念出来。

还需语音控制台确认：已开通产品、独立语音API Key、可用音色、实际计费单价及额度。价格尚未核实，不报未经确认的报价；不购买套餐，不批量调用。密钥只放忽略的本地.env，绝不进入前端或Git。

## 官方来源

- API Key使用：https://docs.volcengine.com/docs/DoubaoVoice/APIKeyUsage?lang=zh
- HTTP流式合成及资源版本：https://docs.volcengine.com/docs/doubao-voice/http-chunked-sse-unidirectional-streaming-v3?lang=zh
- 官方系统音色列表：https://docs.coze.cn/dev_how_to_guides_sys_voice
- 豆包语音音色列表：https://docs.volcengine.com/docs/doubao-voice/tone-list-3?lang=zh
- Agent Plan语音接入：https://docs.volcengine.com/docs/ark/agent-plan-personal-voice-model?lang=zh

## 2026-10-30 密钥接入实测

用户提供语音密钥后，已只保存在被Git忽略的.env（权限0600）。分别发起一次11字符短句测试，无自动重试：

- seed-tts-1.0 / 北京小爷：HTTP 403，服务错误码45000030，`[resource_id=volc.service_type.10029] requested resource not granted`。
- seed-tts-2.0 / 清爽男大2.0（仅作权限测试）：HTTP 403，服务错误码45000030，`[resource_id=volc.seedtts.default] requested resource not granted`。

两次均未返回音频。请求被明确拒绝，预算中登记为api_rejected，不计入成功生成估算；实际结算仍以供应商账单为准。脱敏记录在assets/audio/samples/*/record.json。

下一步检查豆包语音控制台服务开通状态和密钥所属项目资源权限；1.0音色不能替换资源参数直接当2.0调用。未购买资源包、未修改账号权限。

已核对官方2.0按调用后付费价格为3元/万字符（https://docs.volcengine.com/docs/doubao-voice/billing-instructions?lang=zh）。本轮未找到1.0现行按量价格，不套用2.0价格。
