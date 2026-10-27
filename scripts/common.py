import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def read(path):return json.loads(path.read_text())
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');tmp.replace(path)
def digest(data):return hashlib.sha256(data).hexdigest()
def manifest():return read(ROOT/'episodes/ep01/asset_manifest.json')
