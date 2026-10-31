"""Bounded Seed-Audio character and teaching samples. Cache POSTs; never retry an uncertain request."""
import argparse,base64,json,os,subprocess,tempfile,uuid
from common import ROOT,read,write,digest
from generate_assets import dotenv
from production_budget import reserve,synchronize
API='https://openspeech.bytedance.com/api/v3/tts/create'
SAMPLES={
 'chen':('小陈·北京男声','年轻成年男性，北京本地口音，声线清爽、自然亲切，不是播音腔','我是小陈，在这儿帮忙。您先吃着，有事儿叫我。'),
 'owner':('老板娘·北京女声','四十多岁成年女性，北京本地口音，声线温暖略低，干练亲切，不尖细，不装年轻','好嘞，面来了！您慢慢吃，辣椒和醋在这儿。'),
 'gu':('顾承泽·克制北京男声','三十岁左右成年男性，声线中低音，质感沉稳干净，轻微北京本地口音，说话有分寸、有一点疲惫但不虚弱，不是小陈那样的活泼青年声，不压嗓，不装霸总','我叫顾承泽。终于找到你了。这个，是你的。这十个亿，你要不要？'),
 'aunt':('路人阿姨·北京老年女声','六十五岁左右的北京本地老年女性，声线比中年老板娘更年长，略带自然沙感但清楚有气息，温和热心，不尖厉、不颤抖、不像儿童','找面馆啊？往前走，就在右边儿。别着急，慢慢走。'),
 'narrator':('教学旁白·清晰女声','三十岁左右成年女性教学旁白，清澈平稳、亲切专业，与老板娘和老年阿姨明显不同。使用清晰标准普通话，声母韵母与声调准确，不加口语儿化，不改变教学用词','面馆在哪里？我要这个。这个多少钱？我听不懂。')
}
def run(name,execute=False,retry_rejected=False):
 title,voice,line=SAMPLES[name]
 style={'gu':'自然清楚的轻北京口音，语速从容，语气克制认真，句间停顿，最后的问题不凶狠、不喊叫。', 'aunt':'自然清楚的北京老年女性口音，少量自然儿化，语气热心、平易近人，语速适中。','narrator':'标准普通话教学朗读，语速比正常对话慢约20%，每句之间留约1秒停顿，完整自然地读句子，不拆字、不拼读拼音，不加儿化，便于零基础用户模仿。'}.get(name,'用自然清楚的北京口音，少量自然儿化，语速适中，情绪轻松友好，适合零基础中文学习者听清。')
 prompt=f'干净的人声录音，只出现一位说话者，没有背景音乐、没有环境音、没有其他人声。{voice}。{style}不要台湾口音，不要东北口音，不要夸张京剧腔。只说以下台词一次，不朗读任何描述、不加词、不唱歌，约6至10秒，说完即结束：“{line}”'
 if name in ['gu','aunt','narrator']:prompt=prompt.replace('约6至10秒','约10至16秒')
 payload={'model':'seed-audio-1.0','text_prompt':prompt,'audio_config':{'format':'mp3','sample_rate':48000,'pitch_rate':0,'speech_rate':0,'loudness_rate':0},'watermark':{}}
 fp=digest(json.dumps(payload,ensure_ascii=False,sort_keys=True).encode());folder=ROOT/'assets/audio/samples'/('seed-audio-'+name+'-'+fp[:12]);recordpath=folder/'record.json';raw=ROOT/'local/voice-responses'/(fp+'.json')
 if not execute:print(json.dumps({'sample':name,'payload':payload,'reserve_rmb':2},ensure_ascii=False));return
 dotenv();key=os.environ.get('VOLC_VOICE_API_KEY')
 if not key:raise ValueError('Missing local voice credential')
 if recordpath.exists():
  previous=read(recordpath)
  if not retry_rejected or previous['status']!='api_rejected':
   print('CACHED/PRIOR REQUEST',name,previous['status']);return
  attempt=1
  while (folder/f'attempt-{attempt}.json').exists():
   prior=read(folder/f'attempt-{attempt}.json')
   if prior['status']!='api_rejected':raise ValueError('Previous attempt must be resolved before retry')
   attempt+=1
  fp=digest((fp+':attempt:'+str(attempt)).encode());recordpath=folder/f'attempt-{attempt}.json';raw=ROOT/'local/voice-responses'/(fp+'.json')
 folder.mkdir(parents=True,exist_ok=True);raw.parent.mkdir(parents=True,exist_ok=True)
 record={'id':name,'title':title,'text':line,'prompt':prompt,'model':'seed-audio-1.0','fingerprint':fp,'status':'requesting','request_id':str(uuid.uuid4()),'price_basis':'1 RMB/minute original_duration; reserve max 120 seconds = 2 RMB','review_status':'awaiting_listening_review'}
 reserve(ROOT,fp,'VOICE_'+name.upper(),record['model'],2);write(recordpath,record)
 with tempfile.TemporaryDirectory() as td:
  h=__import__('pathlib').Path(td)/'headers';h.write_text('Content-Type: application/json\nX-Api-Key: '+key+'\nX-Api-Request-Id: '+record['request_id']+'\n');h.chmod(0o600)
  body=__import__('pathlib').Path(td)/'request';body.write_text(json.dumps(payload,ensure_ascii=False))
  result=subprocess.run(['curl','--noproxy','*','--silent','--show-error','--max-time','300','--header','@'+str(h),'--data-binary','@'+str(body),'--output',str(raw),'--write-out','%{http_code}',API],capture_output=True,text=True)
 record.update(http_status=result.stdout.strip(),transport_exit=result.returncode);charge=2
 try:
  response=read(raw);record['provider_code']=response.get('code');record['provider_message']=str(response.get('message','')).replace(key,'[REDACTED]')[:1000]
  if result.returncode==0 and result.stdout=='200' and (response.get('audio') or response.get('url')):
   target=folder/'sample.mp3'
   if response.get('audio'):target.write_bytes(base64.b64decode(response['audio'],validate=True))
   else:
    url=response['url']
    if not url.startswith('https://'):raise ValueError('Expected HTTPS audio URL')
    dl=subprocess.run(['curl','--noproxy','*','--silent','--show-error','--fail','--max-time','60','--output',str(target),url],capture_output=True)
    if dl.returncode:raise ValueError('Audio download failed; raw response retained')
   audio=target.read_bytes()
   if len(audio)<1000:raise ValueError('Audio empty or too small')
   duration=float(response['original_duration']);charge=round(duration/60,6)
   record.update(status='generated',audio=str(target.relative_to(ROOT)),sha256=digest(audio),bytes=len(audio),original_duration=duration,duration=response.get('duration'),estimated_rmb=charge)
  else:record['status']='api_rejected' if result.stdout in ['400','401','403'] else 'uncertain'
 except Exception as exc:record.update(status='uncertain',error=type(exc).__name__)
 write(recordpath,record);budget=read(ROOT/'data/production_budget.json');budget['entries'][fp].update(status=record['status'],price_ceiling_rmb=charge);write(ROOT/'data/production_budget.json',budget);synchronize(ROOT)
 print(json.dumps(record,ensure_ascii=False),flush=True)
 if record['status']!='generated':raise SystemExit('Stopped; inspect recorded result before another request')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sample',choices=SAMPLES,required=True);p.add_argument('--execute',action='store_true');p.add_argument('--retry-rejected',action='store_true');a=p.parse_args();run(a.sample,a.execute,a.retry_rejected)
