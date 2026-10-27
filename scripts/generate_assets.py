"""One HTTP request per image. Ambiguous POST failures are never retried automatically."""
import argparse,base64,json,math,mimetypes,os,time,urllib.request,urllib.error,uuid
from common import ROOT,read,write,digest,manifest
API='https://ark.cn-beijing.volces.com/api/v3/images/generations'
def dotenv():
 p=ROOT/'.env'
 if p.exists():
  for line in p.read_text().splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip('\"\''))
def request_json(payload,key):
 req=urllib.request.Request(API,json.dumps(payload).encode(),{'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 # A timeout/5xx may already have incurred cost. Persist uncertainty and stop.
 with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)
def download(url):
 if not url.startswith('https://'):raise ValueError('Image URL must use HTTPS')
 for attempt in range(3):
  try:
   with urllib.request.urlopen(url,timeout=90) as response:return response.read()
  except (OSError,urllib.error.URLError):
   if attempt==2:raise
   time.sleep(2**attempt)
def image_type(data):
 if data.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
 if data.startswith(b'\xff\xd8\xff'):return '.jpg'
 if data[:4]==b'RIFF' and data[8:12]==b'WEBP':return '.webp'
 raise ValueError('Response is not a supported image')
def reference(aid,assets):
 p=ROOT/'assets/approved'/aid/'reference.json'
 if not p.exists():raise ValueError(f'{aid}: approved reference required')
 record=read(p);image=ROOT/record['path'];data=image.read_bytes()
 if digest(data)!=record['sha256']:raise ValueError('Approved reference changed')
 return {'asset_id':aid,'sha256':record['sha256'],'path':record['path']},'data:'+mimetypes.guess_type(image.name)[0]+';base64,'+base64.b64encode(data).decode()
def run(args):
 dotenv();all_assets={a['id']:a for a in manifest()['assets']}
 selected=[all_assets[args.asset_id]] if args.asset_id else list(all_assets.values())
 if args.max_images<1:raise ValueError('--max-images must be positive')
 if not args.dry_run:
  if not args.confirm_paid or args.max_spend_rmb is None or args.unit_price_rmb is None:raise ValueError('Paid run requires --confirm-paid, --unit-price-rmb and --max-spend-rmb based on console price')
  if not math.isfinite(args.unit_price_rmb) or not math.isfinite(args.max_spend_rmb) or args.unit_price_rmb<=0 or args.max_spend_rmb<=0 or args.max_images*args.unit_price_rmb>args.max_spend_rmb:raise ValueError('Invalid or insufficient budget')
  if not os.getenv('ARK_API_KEY'):raise ValueError('ARK_API_KEY missing in local .env')
 count=0;failed=False
 for a in selected:
  if count>=args.max_images:break
  model=args.model or a['model'] or os.getenv('ARK_IMAGE_MODEL');refs=[];images=[];blocked=[]
  for aid in a['reference_assets']:
   try:r,img=reference(aid,all_assets);refs.append(r);images.append(img)
   except ValueError as e:blocked.append(str(e))
  payload={'model':model,'prompt':a['prompt'],'size':a['size'],'response_format':'url','watermark':False}
  if images:payload['image']=images
  fingerprint=digest(json.dumps({'payload':payload,'refs':refs,'candidate':args.candidate},sort_keys=True).encode())
  folder=ROOT/'assets/generated'/a['category']/a['id']/fingerprint
  record_path=folder/'record.json'
  if args.dry_run:
   print(json.dumps({'asset_id':a['id'],'model':model or 'UNCONFIGURED: supply console model/endpoint ID','prompt':a['prompt'],'size':a['size'],'references':refs,'blocked':blocked,'cache_key':fingerprint,'paid':False},ensure_ascii=False));count+=1;continue
  if not model:raise ValueError('Use --model or ARK_IMAGE_MODEL from your console')
  if blocked:raise ValueError('; '.join(blocked))
  if record_path.exists():
   old=read(record_path)
   if old['status'] in ['generated','approved','rejected']:
    if args.resume:
     image=ROOT/old['path']
     if digest(image.read_bytes())!=old['sha256']:raise ValueError('Cached image changed')
     print('CACHED',a['id']);continue
    raise ValueError('Existing candidate: use --resume or a new --candidate label')
   if old['status']=='requesting' or old['status']=='uncertain':raise ValueError('Uncertain paid request; inspect record and provider history before any new candidate')
  else:
   write(record_path,{'asset_id':a['id'],'category':a['category'],'status':'requesting','request_id':str(uuid.uuid4()),'fingerprint':fingerprint,'prompt':a['prompt'],'model':model,'size':a['size'],'references':refs,'price_ceiling_rmb':args.unit_price_rmb,'created_at':time.time()})
  record=read(record_path)
  try:
   if not (folder/'response.json').exists():
    response=request_json(payload,os.environ['ARK_API_KEY']);write(folder/'response.json',response)
   response=read(folder/'response.json');rows=response.get('data',[])
   if len(rows)!=1 or rows[0].get('error'):raise ValueError('Expected exactly one successful image; inspect response')
   row=rows[0];data=base64.b64decode(row['b64_json']) if row.get('b64_json') else download(row['url'])
   suffix=image_type(data);path=folder/('image'+suffix);path.write_bytes(data)
   record.update(status='generated',path=str(path.relative_to(ROOT)),sha256=digest(data));write(record_path,record);print('GENERATED',a['id'],record['path']);count+=1
  except Exception as e:
   record['status']='download_failed' if (folder/'response.json').exists() else 'uncertain';record['error_type']=type(e).__name__;write(record_path,record);print('FAILED',a['id'],record['status']);failed=True;break
 if failed:raise SystemExit(1)
def parser():
 p=argparse.ArgumentParser();p.add_argument('--dry-run',action='store_true');p.add_argument('--asset-id');p.add_argument('--max-images',type=int,default=1);p.add_argument('--max-spend-rmb',type=float);p.add_argument('--unit-price-rmb',type=float);p.add_argument('--model');p.add_argument('--resume',action='store_true');p.add_argument('--confirm-paid',action='store_true');p.add_argument('--candidate',default='1');return p
if __name__=='__main__':
 try:
  args=parser().parse_args()
  if args.dry_run:run(args)
  else:
   lock=ROOT/'local/generation.lock';lock.parent.mkdir(parents=True,exist_ok=True)
   try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
   except FileExistsError:raise ValueError('Generation lock exists; ensure no active run before removing local/generation.lock')
   try:
    os.write(fd,str(os.getpid()).encode());run(args)
   finally:os.close(fd);lock.unlink()
 except (ValueError,KeyError) as e:raise SystemExit(str(e))
