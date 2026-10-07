"""Render all ten tracker families from static evidence; never imply runtime PASS."""
import argparse
import json
from pathlib import Path
CATALOG=(
 ('Building level','building_level_sum','Domestic country building levels; economic ownership and foreign investment scope require verification.'),
 ('GDP','gdp','Currency units, update cadence and numeric precision require verification.'),
 ('Population','total_population','Country/state scope and included populations require verification.'),
 ('Literacy','literacy_rate','0–1 fraction versus displayed percent requires verification.'),
 ('Army size','army_size','Size unit and inclusion of conscripts require verification.'),
 ('Navy size','navy_size','Size unit and active/reserve interpretation require verification.'),
 ('Technology','technology_trigger','Boolean condition; Telephone target only in probe, no fractional research progress.'),
 ('Law','law_trigger','Boolean active-law condition; variants and target selection require verification.'),
 ('Relations','relations','Fixed GBR/FRA target selection in probe; invalid/self/deleted targets must not complete.'),
 ('Country rank','country_rank','Ordinal rank_value thresholds; never a linear percentage.'),
)
def matrix_rows(report):
    rows=[]
    for tracker,key,note in CATALOG:
        api=report['capabilities'][key];d=report['capability_details'][key]
        # Legacy matrix enum cannot express candidate; keep the literal auditor classification in the limitation column.
        status='unsupported' if api=='unsupported' else 'supported-with-limitation'
        paths=d.get('evidence_paths',[])
        rows.append({'tracker':tracker,'api_status':api,'status':status,'evidence':', '.join(paths) if paths else 'No evidence path','limitation':f"{api}: {d['reason']}. {note} runtime verification pending."})
    return rows

def render_matrix(report):
    rows=matrix_rows(report)
    lines=['# Tracker capability matrix','',
           'Static source evidence only. No game runtime has been executed.',
           'The required matrix enum has no candidate value: `supported-with-limitation` with `API status=candidate` means **unproven**, not verified support. All rows retain the auditor classification.',
           '', '| Tracker | Matrix status | API status | Evidence | Limitation |','| --- | --- | --- | --- | --- |']
    for r in rows:
        cells=[r[x].replace('|','\\|').replace('\n',' ') for x in ('tracker','status','api_status','evidence','limitation')]
        lines.append('| '+' | '.join(cells)+' |')
    return '\n'.join(lines)+'\n'

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args(argv)
    if args.evidence.resolve()==args.output.resolve():p.error('Output would overwrite evidence')
    report=json.loads(args.evidence.read_text('utf-8'));text=render_matrix(report)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text,encoding='utf-8');return 0
if __name__=='__main__':raise SystemExit(main())
