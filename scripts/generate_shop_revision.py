"""Bounded shop/decor and speaker-shot revision, one audited request at a time."""
import argparse,subprocess,sys
from common import ROOT,read,write
from generate_candidate_batch import archive
from production_budget import load_budget,total_reserved
PLAN='episodes/ep01/dialogue_asset_plan.json'
def tasks():
 rows=[]
 for aid,old,prompt,model,price in [
  ('BG02_SHOP_MAIN','casting-round-01-3','main','pro',.60),
  ('BG03_COUNTER','derived-round-01-1','counter','flash',.12),
  ('BG04_DOOR','door-clean-01','door','flash',.12),
  ('CG01_FILE_SLAM','cg-pro-expression-v3','cg','pro',.60)]:
  rows.append((aid,'shop-lived-in-v2',price,['--edit-target',f'assets/candidates/{aid}/{old}.jpg','--edit-prompt-file',f'assets/prompts/shop-v2/{prompt}.txt','--model','doubao-seedream-5-0-'+model+('-260628' if model=='pro' else '-260915')]))
 for a in read(ROOT/PLAN)['assets']:rows.append((a['id'],'continuity-v1' if a['id'].startswith('BEAT_') else 'dialogue-v1',.12,['--asset-plan',PLAN]))
 return rows
def main(execute):
 budget=load_budget(ROOT)
 if execute and float(total_reserved(budget))+sum(r[2] for r in tasks())>budget['approved_total_rmb']:raise ValueError('Insufficient remaining project budget')
 completed=[]
 for aid,label,price,extra in tasks():
  cmd=[sys.executable,'scripts/generate_assets.py','--asset-id',aid,'--candidate',label,*extra]
  if execute:cmd+=['--confirm-paid','--resume','--max-images','1','--unit-price-rmb',str(price),'--max-spend-rmb',str(price)]
  else:cmd+=['--dry-run']
  if execute and (ROOT/f'assets/candidates/{aid}/{label}.json').exists():
   completed.append(f'assets/candidates/{aid}/{label}.jpg');continue
  print('REVISION',aid,flush=True);subprocess.run(cmd,cwd=ROOT,check=True)
  if execute:
   completed.append(archive(aid,label));write(ROOT/'docs/checkpoints/shop-v2-generation.json',{'expected_images':len(tasks()),'completed':completed,'all_outputs_await_user_review':True})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');main(p.parse_args().execute)
