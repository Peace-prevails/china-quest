"""Build a static candidate contact sheet; selection is a separate human action."""
import html,json
from pathlib import Path
from common import ROOT,read
GROUPS=[('CH01_OWNER','老板娘（已选定 V3，仅人物）'),('CH02_XIAOCHEN','小陈'),('CH03_GU','顾承泽'),('CH04_RIVAL','陆骁（暂名）'),('BG02_SHOP_MAIN','面馆主场景（独立场景参考）'),('BG03_COUNTER','柜台视角'),('BG04_DOOR','门口视角'),('BG01_HUTONG','胡同外景'),('PR01_BEEF_NOODLES','牛肉面'),('PR02_WATER','矿泉水'),('PR03_ENVELOPE','红色文件袋'),('CG01_FILE_SLAM','关键剧情CG')]

def build():
    sections=[]
    groups=list(GROUPS)
    labels={'DLG_OWNER_WARM':'老板娘 · 招呼客人','DLG_OWNER_GUARDED':'老板娘 · 凝重警惕','DLG_CHEN_FRIENDLY':'小陈 · 轻松介绍','DLG_CHEN_UNSURE':'小陈 · 不确定','DLG_GU_CALM':'顾承泽 · 克制说明','DLG_GU_HESITANT':'顾承泽 · 迟疑','DLG_RIVAL_URGENT':'陆先生 · 急切打断','DLG_AUNT_HELPFUL':'路人阿姨 · 指路'}
    labels.update({'BEAT_MEAL_BEEF':'上菜 · 牛肉面','BEAT_MEAL_ZHAJIANG':'上菜 · 炸酱面','BEAT_GU_ARRIVAL':'顾承泽 · 到店','BEAT_RIVAL_ENTRY':'陆先生 · 闯入'})
    labels.update({'BEAT_EXPLORE_BEEF':'探索全景 · 牛肉面','BEAT_EXPLORE_ZHAJIANG':'探索全景 · 炸酱面'})
    groups.extend(labels.items())
    for aid,title in groups:
        cards=[]
        for path in sorted((ROOT/'assets/candidates'/aid).glob('*.json')):
            data=read(path)
            if aid=='CH01_OWNER' and path.stem!='contour-v3':continue
            image=Path(data['image']).name
            source=aid+'/'+image
            label=path.stem.replace('casting-round-01-','候选 ').replace('independent-round-01-','初稿 ').replace('derived-round-01-','派生 ')
            status=('已选定 · 仅人物，不参考背景' if data.get('reference_scope')=='identity_only' else '已选定 · 场景布局' if data.get('reference_scope')=='scene_layout' else '已选定 · 仅道具' if data.get('reference_scope')=='object_only' else '已选定 · 完整剧情画面') if data['status']=='approved' else {'rejected':'已退回','not_selected':'未选用'}.get(data['status'],'待审阅')
            recommendation=data.get('recommendation','')
            cards.append('<article><a href="'+html.escape(source)+'" target="_blank" rel="noopener"><img loading="lazy" src="'+html.escape(source)+'" alt="'+html.escape(title+' '+label)+'"></a><div><h3>'+html.escape(label)+'</h3><p class="status">'+status+'</p><p>'+html.escape(recommendation)+'</p><details><summary>提示词与记录</summary><p>'+html.escape(data['prompt'])+'</p><a href="'+aid+'/'+path.name+'">JSON 记录</a></details></div></article>')
        sections.append('<section id="'+aid+'"><h2>'+html.escape(title)+'</h2><div class="grid">'+(''.join(cards) if cards else '<p>暂无图片；胡同请求网络失败，已保留费用预留且未自动重发。</p>')+'</div></section>')
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>China Quest · 候选图审阅</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f1ede6;color:#25251e;font:16px/1.65 system-ui,-apple-system,sans-serif}main{max-width:1360px;margin:auto;padding:40px 28px}h1{font-size:32px;margin:0}header p{max-width:760px;color:#645f55}section{margin:48px 0}h2{font-size:23px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px}article{border:1px solid #d9d2c6;background:#fffcf7;border-radius:12px;overflow:hidden}article img{display:block;width:100%;height:450px;object-fit:contain;background:#dfdbd3}article>div{padding:18px}h3{margin:0;font-size:18px}.status{font-size:13px;color:#785b34}details{font-size:13px}details p{white-space:pre-wrap}a{color:#715527}section:last-child img{height:250px}.grid:has(>article:only-child){grid-template-columns:minmax(0,480px)}nav{display:flex;gap:12px;flex-wrap:wrap;margin-top:20px}nav a{background:#e5ded1;border-radius:20px;padding:6px 14px;text-decoration:none;font-size:14px}@media(max-width:800px){article img{height:280px}article>div{padding:12px}main{padding:24px 18px}h1{font-size:26px}}@media(max-width:520px){.grid{grid-template-columns:1fr}article img{height:440px}}
    </style><main><header><h1>China Quest · 人物与场景候选</h1><p>人物图只看面部身份、体态与服装，背景一律不参考。面馆场景独立设计。点击图片查看原图；回复角色名和候选编号即可选定，新版面馆与对话近景已接入游戏供审阅；原始定稿保留，修订版尚未标为用户批准。</p><nav>'''+''.join('<a href="#'+aid+'">'+html.escape(title.split('（')[0])+'</a>' for aid,title in groups)+'''</nav></header>'''+''.join(sections)+'</main></html>'
    path=ROOT/'assets/candidates/review.html';path.write_text(page)
    print(path)
    return path

if __name__=='__main__':build()
