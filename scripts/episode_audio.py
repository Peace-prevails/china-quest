"""Exact-text EP01 audio inventory and resumable, budget-guarded generation."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from common import ROOT,read,write,digest
from story import Story
import generate_voice_samples as voice
ROLES={'OWNER':'owner','XIAOCHEN':'chen','GU':'gu','RIVAL':'rival','aunt':'aunt','narrator':'narrator'}
RIVAL=('陆先生·急切北京男声','三十三岁左右北京成年男性，声线偏中音、粗粝直接，与顾承泽的低沉克制不同，急切但清楚，不喊叫','')
LESSONS=['面馆在哪里？','我要这个。','我不要辣。','这个多少钱？','我听不懂。','这是什么？','那个多少钱？','你是谁？','我不认识你。']
def key(role,text):return hashlib.sha256((role+'\n'+text).encode()).hexdigest()[:20]
def inventory():
 rows={};s=Story()
 def add(role,text,source,spoken=None):
  k=key(role,text)
  if k not in rows:rows[k]={'id':k,'role':role,'text':text,'spoken_text':spoken or text,'sources':[]}
  if source not in rows[k]['sources']:rows[k]['sources'].append(source)
 for food in ['beef','zhajiang']:
  for water in [False,True]:
   s.state.update(item_selected=food,wants_water=water)
   for node in s.data['nodes']:
    s.current=node['id'];n=s.view();role=ROLES[n['speaker']]
    spoken=n['zh']
    if n['id']=='gu_eat':spoken='先让人吃口面！'
    if n['id']=='rival':spoken='等等！不能给你！他认错人了！'
    add(role,n['zh'],'node:'+n['id'],spoken)
    for c in n['choices']:add('narrator',c['zh'],'choice:'+c['id'])
 for text in LESSONS:add('narrator',text,'lesson')
 return list(rows.values())
def publish(rows):
 result=[]
 for row in rows:
  folder=ROOT/'assets/audio/episode'/row['id'];rp=folder/'record.json'
  if not rp.exists():continue
  r=read(rp)
  if r.get('status')!='generated':continue
  path=ROOT/r['audio'];assert digest(path.read_bytes())==r['sha256']
  result.append({**row,'audio':r['audio'],'sha256':r['sha256'],'review_status':'generated_preview'})
 write(ROOT/'episodes/ep01/audio_manifest.json',{'status':'generated_preview','note':'Voice directions accepted; each generated line still needs listening review. Exact text lookup; no sample substitution.','expected_count':len(rows),'clips':result})
 return len(result)
def main():
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');p.add_argument('--limit',type=int,default=200);a=p.parse_args();rows=inventory();write(ROOT/'assets/audio/episode_plan.json',rows)
 if not a.execute:print('Planned unique exact-text clips:',len(rows));return
 pending=[]
 for row in rows:
  rp=ROOT/'assets/audio/episode'/row['id']/'record.json'
  if rp.exists():
   if read(rp)['status']!='generated':raise RuntimeError('Resolve prior request before proceeding: '+row['id'])
  else:pending.append(row)
 def generate(row):
  folder=ROOT/'assets/audio/episode'/row['id'];role=row['role'];title,description,_=RIVAL if role=='rival' else voice.SAMPLES[role]
  voice.run(role,execute=True,custom=(title,description,row['spoken_text']),output_folder=folder,short_line=True)
  record=read(folder/'record.json');assert record['status']=='generated'
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_name','-of','json',str(ROOT/record['audio'])]))
  assert probe['streams'][0]['codec_name']=='mp3' and float(probe['format']['duration'])>0
 # Fixed batches bound outstanding costs. Finish in-flight requests before stopping on failure.
 from concurrent.futures import ThreadPoolExecutor
 pending=pending[:a.limit]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for start in range(0,len(pending),4):
   futures=[pool.submit(generate,row) for row in pending[start:start+4]]
   for future in futures:future.result()
   print('PROGRESS',publish(rows),'/',len(rows),flush=True)
 print('COMPLETE',publish(rows),'/',len(rows),flush=True)
if __name__=='__main__':main()
