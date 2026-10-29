"""Fixed casting round: three candidates each; one paid request at a time."""
import argparse,json,subprocess,sys,hashlib,shutil
from common import ROOT,read,write
from production_budget import load_budget,total_reserved,synchronize
ASSETS=['CH02_XIAOCHEN','CH03_GU','CH04_RIVAL','BG02_SHOP_MAIN']
LABEL='casting-round-01'
PRICE=0.12

def archive(asset_id,label):
    records=[]
    for path in (ROOT/'assets/generated').rglob('record.json'):
        record=read(path)
        if record['asset_id']!=asset_id or record['status'] not in ['generated','approved','rejected']:continue
        fingerprint=record['fingerprint']
        # Candidate label is persisted by generate_assets for auditable lookup.
        if record.get('candidate')!=label:continue
        records.append((path,record))
    if len(records)!=1:raise ValueError('Expected exactly one completed candidate for '+label)
    path,record=records[0];image=ROOT/record['path'];content=image.read_bytes()
    if hashlib.sha256(content).hexdigest()!=record['sha256']:raise ValueError('Archive integrity check failed')
    target=ROOT/'assets/candidates'/asset_id/(label+image.suffix);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and target.read_bytes()!=content:raise ValueError('Refusing to overwrite a candidate archive')
    if not target.exists():shutil.copyfile(image,target)
    metadata={key:record[key] for key in ['asset_id','model','prompt','size','references','sha256','price_ceiling_rmb','fingerprint','candidate']}
    metadata.update(status='awaiting_human_review',image=str(target.relative_to(ROOT)),reference_scope={'backgrounds':'scene_layout','characters':'identity_only','props':'object_only','cg':'full_image'}[record['category']],background_is_reference=asset_id.startswith('BG'),validation={'downloaded':True,'sha256_matches':True})
    write(target.with_suffix('.json'),metadata)
    return str(target.relative_to(ROOT))

def main(execute=False,phase='casting'):
    label_root={'casting':LABEL,'independent':'independent-round-01','derived':'derived-round-01'}[phase]
    selected={'casting':ASSETS,'independent':['BG01_HUTONG','PR01_BEEF_NOODLES','PR02_WATER','PR03_ENVELOPE'],'derived':['BG03_COUNTER','BG04_DOOR']}[phase]
    per_asset=3 if phase=='casting' else 1
    plan=[(aid,f'{label_root}-{i}') for aid in selected for i in range(1,per_asset+1)]
    if not execute:
        print(json.dumps({'images':len(plan),'estimated_rmb':round(len(plan)*PRICE,2),'plan':plan},ensure_ascii=False,indent=2))
        for aid,label in plan:
            subprocess.run([sys.executable,'scripts/generate_assets.py','--dry-run','--asset-id',aid,'--candidate',label,'--max-images','1'],cwd=ROOT,check=True)
        return
    budget=load_budget(ROOT)
    if budget is None:raise ValueError('Persistent project budget required for batch')
    # Conservative preflight reserves full batch even when some are already cached.
    if float(total_reserved(budget))+len(plan)*PRICE>budget['approved_total_rmb']:raise ValueError('Insufficient cumulative budget')
    archived=[]
    for aid,label in plan:
        command=[sys.executable,'scripts/generate_assets.py','--asset-id',aid,'--candidate',label,'--max-images','1','--unit-price-rmb',str(PRICE),'--max-spend-rmb',str(len(plan)*PRICE),'--confirm-paid','--resume']
        print('CANDIDATE',aid,label,flush=True)
        subprocess.run(command,cwd=ROOT,check=True)
        archived.append(archive(aid,label))
        write(ROOT/'docs/checkpoints'/f'{label_root}-inventory.json',{'batch':label_root,'planned_images':len(plan),'completed_images':len(archived),'archives':archived,'actual_billing_queried':False})
    synchronize(ROOT)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--phase',choices=['casting','independent','derived'],default='casting');args=parser.parse_args()
    main(args.execute,args.phase)
