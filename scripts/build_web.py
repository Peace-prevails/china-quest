"""Package only public story files and hash-verified approved assets for local play."""
import shutil
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
 for source in (ROOT/'web').iterdir():
  if source.suffix in ['.html','.css','.mjs','.json']:shutil.copyfile(source,output/source.name)
 shutil.copyfile(ROOT/'episodes/ep01/episode_01.json',output/'episode.json')
 write(output/'assets.json',assets)
 print(output)
 return output
if __name__=='__main__':build()
