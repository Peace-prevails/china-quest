"""One HTTP request per image. Ambiguous POST failures are never retried automatically."""
import argparse,base64,email,io,json,math,mimetypes,os,subprocess,tempfile,time,urllib.request,urllib.error,uuid
from common import ROOT,read,write,digest,manifest
from production_budget import reserve,synchronize
API='https://ark.cn-beijing.volces.com/api/v3/images/generations'
def dotenv():
 p=ROOT/'.env'
 if p.exists():
  for line in p.read_text().splitlines():
   if line.strip() and not line.lstrip().startswith('#') and '=' in line:
    k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip().strip('\"\''))
def http_error_details(error,key=''):
 """Retain useful provider diagnostics, never credentials or response headers wholesale."""
 try:body=error.read(65536).decode('utf-8',errors='replace')
 finally:error.close()
 if key:body=body.replace(key,'[REDACTED]')
 try:
  parsed=json.loads(body);provider=parsed.get('error',{})
  if not isinstance(provider,dict):provider={}
 except (ValueError,AttributeError):provider={}
 details={'status':error.code}
 for field in ['code','type','message','param']:
  value=provider.get(field)
  if isinstance(value,(str,int)):details[field]=str(value)[:3000]
 request_id=error.headers.get('x-request-id') or error.headers.get('x-tt-logid') if error.headers else None
 if request_id:details['request_id']=request_id
 if not provider:details['body_excerpt']=body[:1000]
 return details
def curl_request_json(payload,key):
 # Keep the key out of argv, shell history and printed diagnostics.
 with tempfile.TemporaryDirectory(prefix='china-quest-ark-') as folder:
  from pathlib import Path
  directory=Path(folder);body=directory/'request.json';headers=directory/'headers';response=directory/'response.json';received_headers=directory/'response.headers'
  body.write_text(json.dumps(payload));headers.write_text('Authorization: Bearer '+key+'\nContent-Type: application/json\n');headers.chmod(0o600)
  command=['curl','--silent','--show-error','--fail-with-body','--connect-timeout','20','--max-time','180','--retry','0','--header','@'+str(headers),'--data-binary','@'+str(body),'--output',str(response),'--dump-header',str(received_headers),'--write-out','%{http_code}',API]
  result=subprocess.run(command,capture_output=True,text=True)
  content=response.read_bytes() if response.exists() else b''
  status=int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
  if status>=400:
   raw=received_headers.read_text(errors='replace') if received_headers.exists() else ''
   block=raw.rstrip().split('\n\n')[-1]
   parsed=email.message_from_string('\n'.join(block.splitlines()[1:]))
   raise urllib.error.HTTPError(API,status,'Ark rejected request',parsed,io.BytesIO(content))
  if result.returncode:raise urllib.error.URLError('curl transport: '+result.stderr.replace(key,'[REDACTED]')[:1000])
  return json.loads(content)
def request_json(payload,key):
 if os.getenv('ARK_HTTP_TRANSPORT')=='curl':return curl_request_json(payload,key)
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
 record=read(p);image=(ROOT/record['path']).resolve()
 if not image.is_relative_to((ROOT/'assets/approved'/aid).resolve()):raise ValueError('Reference must be inside its approved asset directory')
 data=image.read_bytes()
 if digest(data)!=record['sha256']:raise ValueError('Approved reference changed')
 return {'asset_id':aid,'sha256':record['sha256'],'path':record['path'],'scope':record.get('reference_scope','full_image')},'data:'+mimetypes.guess_type(image.name)[0]+';base64,'+base64.b64encode(data).decode()
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
  if getattr(args,'edit_target',None):
   target=(ROOT/args.edit_target).resolve()
   if not target.is_relative_to((ROOT/'assets/candidates').resolve()):raise ValueError('Edit target must be an archived candidate')
   data=target.read_bytes();image_type(data)
   metadata=read(target.with_suffix('.json'))
   if metadata['asset_id']!=a['id'] or digest(data)!=metadata['sha256']:raise ValueError('Edit target identity or hash mismatch')
   if not getattr(args,'edit_prompt_file',None):raise ValueError('Edit requires an explicit prompt file')
   refs=[{'asset_id':a['id'],'sha256':digest(data),'path':str(target.relative_to(ROOT.resolve())),'scope':'edit_target'}]
   images=['data:'+mimetypes.guess_type(target.name)[0]+';base64,'+base64.b64encode(data).decode()];blocked=[]
  scope_notes=[]
  for index,ref in enumerate(refs,1):
   if ref['scope']=='identity_only':
    if a['category']=='backgrounds':raise ValueError('An identity-only reference cannot define a background')
    scope_notes.append(f'参考图{index}（{ref["asset_id"]}）只参考人物的面部身份、体态和已确认服装；完全忽略该图背景、空间布局、道具与光线，以目标场景指令为准。')
   elif ref['scope']=='scene_layout':scope_notes.append(f'参考图{index}（{ref["asset_id"]}）仅约束场景布局、建筑材质与室内陈设。')
   elif ref['scope']=='object_only':scope_notes.append(f'参考图{index}（{ref["asset_id"]}）只参考主体物品，忽略其背景。')
  base_prompt=(ROOT/args.edit_prompt_file).read_text() if getattr(args,'edit_target',None) else a['prompt']
  effective_prompt=base_prompt+('\n'+'\n'.join(scope_notes) if scope_notes else '')
  payload={'model':model,'prompt':effective_prompt,'size':a['size'],'response_format':'url','watermark':False}
  if images:payload['image']=images
  fingerprint=digest(json.dumps({'payload':payload,'refs':refs,'candidate':args.candidate},sort_keys=True).encode())
  folder=ROOT/'assets/generated'/a['category']/a['id']/fingerprint
  record_path=folder/'record.json'
  if args.dry_run:
   print(json.dumps({'asset_id':a['id'],'model':model or 'UNCONFIGURED: supply console model/endpoint ID','prompt':effective_prompt,'size':a['size'],'references':refs,'blocked':blocked,'cache_key':fingerprint,'paid':False},ensure_ascii=False));count+=1;continue
  if not model:raise ValueError('Use --model or ARK_IMAGE_MODEL from your console')
  if blocked:raise ValueError('; '.join(blocked))
  if record_path.exists():
   old=read(record_path)
   if old['status'] in ['generated','approved','rejected']:
    if args.resume:
     image=ROOT/old['path']
     if digest(image.read_bytes())!=old['sha256']:raise ValueError('Cached image changed')
     print('CACHED',a['id']);count+=1;continue
    raise ValueError('Existing candidate: use --resume or a new --candidate label')
   if old['status']=='request_rejected':raise ValueError('Request was rejected; fix the recorded cause and use a new candidate label for an audited retry')
   if old['status'] in ['requesting','uncertain'] and not (folder/'response.json').exists():raise ValueError('Uncertain paid request; inspect record and provider history before any new candidate')
  else:
   reserve(ROOT,fingerprint,a['id'],model,args.unit_price_rmb)
   write(record_path,{'asset_id':a['id'],'category':a['category'],'status':'requesting','request_id':str(uuid.uuid4()),'fingerprint':fingerprint,'candidate':args.candidate,'prompt':effective_prompt,'model':model,'size':a['size'],'references':refs,'price_ceiling_rmb':args.unit_price_rmb,'created_at':time.time()})
  record=read(record_path)
  try:
   if not (folder/'response.json').exists():
    response=request_json(payload,os.environ['ARK_API_KEY']);write(folder/'response.json',response)
   response=read(folder/'response.json');rows=response.get('data',[])
   if len(rows)!=1 or rows[0].get('error'):raise ValueError('Expected exactly one successful image; inspect response')
   row=rows[0];data=base64.b64decode(row['b64_json']) if row.get('b64_json') else download(row['url'])
   suffix=image_type(data);path=folder/('image'+suffix)
   temporary=folder/('image'+suffix+'.tmp');temporary.write_bytes(data);temporary.replace(path)
   record.update(status='generated',path=str(path.relative_to(ROOT)),sha256=digest(data));write(record_path,record);synchronize(ROOT);print('GENERATED',a['id'],record['path']);count+=1
  except Exception as e:
   record['status']='download_failed' if (folder/'response.json').exists() else 'uncertain'
   record['error_type']=type(e).__name__
   if isinstance(e,urllib.error.URLError) and not isinstance(e,urllib.error.HTTPError):
    record['network_error']=str(e.reason).replace(os.environ.get('ARK_API_KEY',''),'[REDACTED]')[:1000] if os.environ.get('ARK_API_KEY') else str(e.reason)[:1000]
   if isinstance(e,urllib.error.HTTPError):
    details=http_error_details(e,os.environ.get('ARK_API_KEY',''))
    record['http_error']=details
    if record['status']=='uncertain' and e.code in [400,401,403,404,405,413,415,422]:record['status']='request_rejected'
   write(record_path,record);synchronize(ROOT)
   print('FAILED',a['id'],record['status'])
   if record.get('network_error'):print('NETWORK',record['network_error'])
   if record.get('http_error'):print(json.dumps(record['http_error'],ensure_ascii=False))
   failed=True;break
 if failed:raise SystemExit(1)
def parser():
 p=argparse.ArgumentParser();p.add_argument('--edit-target');p.add_argument('--edit-prompt-file');p.add_argument('--dry-run',action='store_true');p.add_argument('--asset-id');p.add_argument('--max-images',type=int,default=1);p.add_argument('--max-spend-rmb',type=float);p.add_argument('--unit-price-rmb',type=float);p.add_argument('--model');p.add_argument('--resume',action='store_true');p.add_argument('--confirm-paid',action='store_true');p.add_argument('--candidate',default='1');return p
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
