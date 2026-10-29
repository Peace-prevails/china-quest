"""Inspect candidate inventory and readiness without making network requests."""
import argparse
from common import ROOT, manifest, read, write, digest
from production_budget import load_budget,total_reserved


def inventory():
    data=manifest(); rows=[]
    for asset in data['assets']:
        records=[]
        for path in sorted((ROOT/'assets/generated'/asset['category']/asset['id']).glob('*/record.json')):
            records.append(read(path))
        reference=ROOT/'assets/approved'/asset['id']/'reference.json'
        approved=None; errors=[]
        if reference.exists():
            try:
                approved=read(reference)
                image=(ROOT/approved['path']).resolve()
                if not image.is_relative_to(reference.parent.resolve()) or digest(image.read_bytes())!=approved['sha256']:
                    raise ValueError('Approved reference integrity failed')
            except (OSError, ValueError, KeyError) as error:
                errors.append(type(error).__name__);approved=None
        rows.append({'id':asset['id'],'category':asset['category'],'candidate_target':asset['candidate_target'],
                     'candidates':len(records),'statuses':{status:sum(r['status']==status for r in records) for status in sorted({r['status'] for r in records})},
                     'approved_reference_image':approved['path'] if approved else None,
                     'errors':errors,'dependencies':asset['reference_assets']})
    approved_ids={row['id'] for row in rows if row['approved_reference_image']}
    for row in rows:
        row['blocked_by']=[aid for aid in row['dependencies'] if aid not in approved_ids]
        row['ready_for_generation']=not row['blocked_by'] and not row['errors']
    budget=load_budget(ROOT)
    return {'base_assets':len(rows),'candidate_target_total':sum(row['candidate_target'] for row in rows),
            'approved_assets':len(approved_ids),'assets':rows,'paid_generation_authorized':bool(budget),'budget':{'approved_total_rmb':budget['approved_total_rmb'],'estimated_and_reserved_rmb':float(total_reserved(budget))} if budget else None}


def export_approved(path):
    report=inventory()
    if report['approved_assets']!=report['base_assets']:
        raise ValueError(f'Only {report["approved_assets"]}/{report["base_assets"]} approved; production export refused')
    data=manifest()
    by_id={row['id']:row for row in report['assets']}
    for asset in data['assets']:
        row=by_id[asset['id']]
        asset['approved_reference_image']=row['approved_reference_image']
    write(path,data)


if __name__=='__main__':
    import json,pathlib
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=pathlib.Path);parser.add_argument('--export-approved',type=pathlib.Path);args=parser.parse_args()
    try:
        if args.export_approved:export_approved(args.export_approved)
        report=inventory()
        if args.output:write(args.output,report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except ValueError as error:raise SystemExit(str(error))
