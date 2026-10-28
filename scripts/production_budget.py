"""Cumulative project budget; retain allocations even if local images are moved."""
from decimal import Decimal
from common import read,write
RESERVED={'requesting','uncertain','download_failed','generated','approved','rejected'}

def load_budget(root):
    path=root/'data/production_budget.json'
    if not path.exists():return None
    budget=read(path)
    entries=budget.setdefault('entries',{})
    for record_path in (root/'assets/generated').rglob('record.json'):
        record=read(record_path)
        entries[record['fingerprint']]={key:record.get(key) for key in ['asset_id','model','status','price_ceiling_rmb']}
    return budget

def total_reserved(budget):
    return sum((Decimal(str(entry['price_ceiling_rmb'])) for entry in budget['entries'].values() if entry['status'] in RESERVED),Decimal(0))

def reserve(root,fingerprint,asset_id,model,price):
    budget=load_budget(root)
    if budget is None:return
    if fingerprint in budget['entries']:raise ValueError('Budget allocation already exists; inspect prior request before new POST')
    charge=Decimal(str(price))
    if not charge.is_finite() or charge<=0:raise ValueError('Invalid budget allocation')
    if total_reserved(budget)+charge>Decimal(str(budget['approved_total_rmb'])):raise ValueError('Cumulative project budget would be exceeded')
    budget['entries'][fingerprint]={'asset_id':asset_id,'model':model,'status':'requesting','price_ceiling_rmb':price}
    write(root/'data/production_budget.json',budget)

def synchronize(root):
    budget=load_budget(root)
    if budget is None:return
    used=total_reserved(budget)
    budget['reserved_and_estimated_rmb']=float(used)
    budget['remaining_estimate_rmb']=float(Decimal(str(budget['approved_total_rmb']))-used)
    write(root/'data/production_budget.json',budget)
    return budget
