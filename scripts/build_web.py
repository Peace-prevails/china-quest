"""Package only public story files and hash-verified approved assets for local play."""
import shutil,re
from common import ROOT,read,write,digest

def build():
 output=ROOT/'local/web';output.mkdir(parents=True,exist_ok=True)
 manifest=read(ROOT/'episodes/ep01/approved_asset_manifest.json');assets={}
 for asset in manifest['assets']:
  reference=read(ROOT/'assets/approved'/asset['id']/'reference.json')
  source=(ROOT/reference['path']).resolve()
  if not source.is_relative_to((ROOT/'assets/approved').resolve()) or digest(source.read_bytes())!=reference['sha256']:raise ValueError('Approved asset integrity failed')
  if asset['approved_reference_image']!=reference['path']:raise ValueError('Manifest and approval differ')
  target=output/'images'/source.name;target.parent.mkdir(exist_ok=True)
  shutil.copyfile(source,target);assets[asset['id']]='images/'+source.name
 # Revised shots are explicitly a review preview; original approvals stay immutable.
 revision_path=ROOT/'episodes/ep01/visual_revision.json'
 if revision_path.exists():
  revision=read(revision_path)
  if revision.get('status')!='review_preview':raise ValueError('Unknown visual revision status')
  for aid,row in revision['assets'].items():
   source=(ROOT/row['path']).resolve()
   if not source.is_relative_to((ROOT/'assets/candidates').resolve()):raise ValueError('Preview asset must be archived')
   metadata=read(source.with_suffix('.json'))
   if metadata['asset_id']!=aid or metadata['sha256']!=row['sha256'] or digest(source.read_bytes())!=row['sha256']:raise ValueError('Preview asset integrity failed')
   if not metadata.get('visual_review_complete'):raise ValueError('Visual QA required before preview')
   target=output/'images'/(row['sha256']+source.suffix);shutil.copyfile(source,target);assets[aid]='images/'+target.name
  write(output/'visual_revision.json',{'status':revision['status'],'revision':revision['revision']})
 sources=sorted((ROOT/'web').iterdir())
 version=digest(b''.join(p.read_bytes() for p in sources if p.suffix in ['.html','.css','.mjs','.json'])+b''.join(p.read_bytes() for p in (ROOT/'episodes/ep01').glob('*.json')))[:12]
 for source in sources:
  if source.suffix in ['.html','.css','.mjs','.json']:
   if source.suffix in ['.html','.mjs']:
    content=re.sub(r'([\w./-]+\.(?:mjs|css))([\"\'])',lambda m:m[1]+'?v='+version+m[2],source.read_text())
    content=content.replace('fetch(path)',f"fetch(path+'?v={version}')").replace("fetch('audio.json')",f"fetch('audio.json?v={version}')")
    (output/source.name).write_text(content)
   else:shutil.copyfile(source,output/source.name)
 shutil.copyfile(ROOT/'episodes/ep01/episode_01.json',output/'episode.json')
 write(output/'assets.json',assets)
 audio_path=ROOT/'episodes/ep01/audio_manifest.json';clips=[]
 if audio_path.exists():
  for row in read(audio_path)['clips']:
   source=(ROOT/row['audio']).resolve()
   if not source.is_relative_to((ROOT/'assets/audio/episode').resolve()) or digest(source.read_bytes())!=row['sha256']:raise ValueError('Audio integrity failed')
   target=output/'audio'/(row['sha256']+'.mp3');target.parent.mkdir(exist_ok=True);shutil.copyfile(source,target)
   clips.append({'role':row['role'],'text':row['text'],'audio':'audio/'+target.name})
 write(output/'audio.json',{'clips':clips})
 print(output)
 return output
if __name__=='__main__':build()
