import argparse,html,shutil
from common import ROOT,read,write,digest

def review(record_path,status,note):
 if status not in ['approved','rejected']:raise ValueError('Invalid review decision')
 if not note or not note.strip():raise ValueError('Review note is required')
 path=record_path.resolve()
 if not path.is_relative_to((ROOT/'assets/generated').resolve()):raise ValueError('Record must be inside generated assets')
 record=read(path)
 if record['status']!='generated':raise ValueError('Only a downloaded, unreviewed candidate may be reviewed')
 image=(ROOT/record['path']).resolve()
 if not image.is_relative_to((ROOT/'assets/generated').resolve()) or digest(image.read_bytes())!=record['sha256']:raise ValueError('Candidate integrity check failed')
 if status=='approved':
  folder=(ROOT/'assets/approved'/record['asset_id']).resolve()
  if folder.parent != (ROOT/'assets/approved').resolve():raise ValueError('Invalid asset ID')
  folder.mkdir(parents=True,exist_ok=True)
  target=folder/(record['sha256']+image.suffix)
  reference=folder/'reference.json'
  if reference.exists():raise ValueError('Reference already locked; do not overwrite approved identity')
  if target.exists() and digest(target.read_bytes())!=record['sha256']:raise ValueError('Existing approved file failed integrity check')
  if not target.exists():shutil.copyfile(image,target)
  write(reference,{'asset_id':record['asset_id'],'path':str(target.relative_to(ROOT)),'sha256':record['sha256'],'review_note':note,'source_record':str(path.relative_to(ROOT))})
 record.update(status=status,review_note=note);write(path,record)
def gallery():
 cards=[]
 for path in sorted((ROOT/'assets/generated').rglob('record.json')):
  r=read(path)
  if 'path' not in r:continue
  src='../../'+r['path'];cards.append(f'<article><h2>{html.escape(r["asset_id"])}</h2><img src="{html.escape(src)}"><p>{html.escape(r["status"])}</p><code>{html.escape(str(path.relative_to(ROOT)))}</code></article>')
 p=ROOT/'local/review/index.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('<!doctype html><meta charset="utf-8"><title>China Quest review</title><style>body{font-family:system-ui;background:#eee;padding:24px}article{background:white;padding:20px;margin:20px}img{max-width:100%;max-height:600px}code{overflow-wrap:anywhere}</style><h1>人工审核候选图</h1><p>检查面部身份、场景布局、手部、无乱码。角色透明度需另行抠图审核，批准照片不等于透明立绘。</p>'+''.join(cards));print(p)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record',type=__import__('pathlib').Path);p.add_argument('--decision',choices=['approved','rejected']);p.add_argument('--note');a=p.parse_args()
 if a.record:
  if not a.decision or not a.note:p.error('Review requires decision and note')
  review(a.record,a.decision,a.note)
 else:gallery()
