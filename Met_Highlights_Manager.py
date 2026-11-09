#!/usr/bin/env python3
"""Met Highlights Manager: refresh CSV, snapshot CC0 highlights, resume gentle image downloads."""
import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path
import random
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GITHUB_API = 'https://api.github.com/repos/metmuseum/openaccess/commits?path=MetObjects.csv&per_page=1'
CSV_URL = 'https://media.githubusercontent.com/media/metmuseum/openaccess/master/MetObjects.csv'
API_URL = 'https://collectionapi.metmuseum.org/public/collection/v1/objects/'
AGENT = 'EO1-Museum-Met-Highlights-Manager/1.0 (personal open-access archive)'

def now():
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')

def request(url, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': AGENT, 'Accept':'application/json, */*'}), timeout=timeout)

def get_json(url, attempts=3):
    for i in range(attempts):
        try:
            with request(url) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            if i == attempts - 1: raise
            time.sleep(3 * (i+1))

def remote_revision():
    try:
        commit = get_json(GITHUB_API)[0]
        return {'sha':commit['sha'], 'date':commit['commit']['committer']['date']}
    except Exception as e:
        print(f'[WARN] GitHub update check unavailable: {e}')
        return None

def valid_csv(path):
    if not path.is_file() or path.stat().st_size < 1000000: return False
    try:
        with path.open(encoding='utf-8-sig', newline='') as f:
            fields = csv.reader(f).__next__()
            return {'Object ID','Is Highlight','Is Public Domain'}.issubset(fields)
    except Exception: return False

def download_csv(dest):
    tmp = dest.with_name(dest.name + '.part')
    print('[CSV] Downloading updated MetObjects.csv (hundreds of MB)...')
    try:
        with request(CSV_URL, timeout=90) as r, tmp.open('wb') as f:
            while True:
                chunk = r.read(1024*1024)
                if not chunk: break
                f.write(chunk)
        if not valid_csv(tmp):
            raise RuntimeError('Downloaded file is not a valid MetObjects.csv (possible Git LFS pointer).')
        os.replace(tmp, dest)
    finally:
        if tmp.exists(): tmp.unlink()

def ensure_csv(path, statefile, no_update=False):
    state = {}
    if statefile.exists():
        try: state = json.loads(statefile.read_text(encoding='utf-8'))
        except (ValueError, OSError): pass
    local_ok = valid_csv(path)
    remote = None if no_update else remote_revision()
    needs = not local_ok
    if local_ok and remote:
        if state.get('csv_commit_sha'):
            needs = state['csv_commit_sha'] != remote['sha']
        else:
            remote_date = dt.datetime.fromisoformat(remote['date'].replace('Z','+00:00')).timestamp()
            needs = remote_date > path.stat().st_mtime
            if not needs:
                print('[CSV] Local CSV appears newer than latest GitHub commit; retaining it.')
    if needs:
        if not remote and local_ok:
            print('[CSV] Cannot verify remote freshness; retaining existing CSV.')
            needs = False
        else:
            try:
                download_csv(path)
                if remote:
                    state['csv_commit_sha'] = remote['sha']
                    state['csv_commit_date'] = remote['date']
                state['csv_downloaded_at'] = now()
                statefile.write_text(json.dumps(state, indent=2), encoding='utf-8')
            except Exception as e:
                if not local_ok: raise
                print(f'[WARN] Update failed; using existing CSV: {e}')
    if not valid_csv(path): raise RuntimeError(f'No usable CSV: {path}')
    print(f'[CSV] Using {path} ({path.stat().st_size/1024/1024:.1f} MiB)')
    return state

def make_snapshot(csvpath, outdir):
    date = dt.datetime.now().strftime('%Y-%m-%d')
    dest = outdir / f'Met_highlights_public_domain_{date}.csv'
    temp = dest.with_name(dest.name+'.part')
    count = 0
    with csvpath.open(encoding='utf-8-sig', newline='') as src, temp.open('w', encoding='utf-8', newline='') as dst:
        reader = csv.DictReader(src)
        if not reader.fieldnames or not {'Object ID','Is Highlight','Is Public Domain'}.issubset(reader.fieldnames):
            raise RuntimeError('CSV columns missing.')
        writer = csv.DictWriter(dst, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row['Is Highlight'].strip().lower() in ('true','1') and row['Is Public Domain'].strip().lower() in ('true','1'):
                writer.writerow(row); count += 1
    os.replace(temp, dest)
    print(f'[FILTER] {count} public-domain highlights -> {dest}')
    return dest, count

def read_manifest(path):
    records = {}
    if path.exists():
        with path.open(encoding='utf-8-sig', newline='') as f:
            for r in csv.DictReader(f):
                if r.get('Object ID'): records[r['Object ID']] = r
    return records

FIELDS = ['Object ID','Title','Department','Status','Filename','Bytes','Image URL','Checked At','Error']
def save_manifest(path, records):
    tmp = path.with_name(path.name+'.part')
    with tmp.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f, fieldnames=FIELDS, extrasaction='ignore'); w.writeheader()
        for k in sorted(records, key=lambda s:int(s) if s.isdigit() else s): w.writerow(records[k])
    os.replace(tmp,path)

def safe_image_url(url):
    parsed=urllib.parse.urlparse(url)
    return parsed.scheme=='https' and parsed.hostname and (parsed.hostname=='metmuseum.org' or parsed.hostname.endswith('.metmuseum.org'))

def encode_image_url(url):
    """Percent-encode unsafe characters in image URL paths (e.g. spaces)."""
    parts = urllib.parse.urlsplit(url)
    path = urllib.parse.quote(parts.path, safe="/%:@!$&'()*+,;=-._~")
    query = urllib.parse.quote(parts.query, safe="%=&;/:?@!$'()*+,~-._")
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, path, query, parts.fragment))


def download_image(url, target, max_bytes=80*1024*1024):
    temp=target.with_name(target.name+'.part')
    try:
        with request(encode_image_url(url),timeout=60) as resp, temp.open('wb') as f:
            ctype=resp.headers.get('Content-Type','').lower()
            if not ctype.startswith('image/'):
                raise RuntimeError(f'Unexpected content type: {ctype}')
            size=0
            while True:
                chunk=resp.read(1024*1024)
                if not chunk: break
                size+=len(chunk)
                if size>max_bytes: raise RuntimeError('Image exceeds 80 MiB limit')
                f.write(chunk)
        if size<1024: raise RuntimeError('Image too small')
        os.replace(temp,target)
        return size
    finally:
        if temp.exists(): temp.unlink()

def run(args):
    root=Path(args.directory).resolve()
    root.mkdir(parents=True,exist_ok=True)
    csvpath=Path(args.csv).resolve()
    statefile=root/'csv_source_state.json'
    ensure_csv(csvpath,statefile,args.no_update)
    snapshot,total=make_snapshot(csvpath,root)
    if args.snapshot_only:
        print('[DONE] Snapshot only; no API or image downloads.')
        return
    images=root/'images'; images.mkdir(exist_ok=True)
    manifest=root/'download_manifest.csv'
    records=read_manifest(manifest)
    with snapshot.open(encoding='utf-8',newline='') as f:
        candidates=list(csv.DictReader(f))
    pending=[]
    for row in candidates:
        oid=row['Object ID'].strip()
        if not oid.isdigit(): continue
        old=records.get(oid,{})
        name=old.get('Filename','')
        if old.get('Status')=='downloaded' and name and (images/name).is_file() and (images/name).stat().st_size>1024:
            continue
        if old.get('Status')=='no_image' and not args.retry_missing:
            continue
        pending.append(row)
    print(f'[DOWNLOAD] {len(pending)} pending; {total-len(pending)} already completed/skipped.')
    if args.limit: pending=pending[:args.limit]
    done=0
    try:
        for n,row in enumerate(pending,1):
            oid=row['Object ID'].strip()
            item={'Object ID':oid,'Title':row.get('Title',''),'Department':row.get('Department',''),
                  'Status':'','Filename':'','Bytes':'','Image URL':'','Checked At':now(),'Error':''}
            try:
                data=get_json(API_URL+oid)
                if not data.get('isPublicDomain',False):
                    item['Status']='not_public_domain'
                else:
                    url=data.get('primaryImage') or data.get('primaryImageSmall') or ''
                    if not url:
                        item['Status']='no_image'
                    elif not safe_image_url(url):
                        item['Status']='error'; item['Error']='Unexpected image host'
                    else:
                        extension=Path(urllib.parse.urlparse(url).path).suffix.lower()
                        if extension not in ('.jpg','.jpeg','.png','.webp','.tif','.tiff'): extension='.jpg'
                        filename=oid+extension
                        target=images/filename
                        if target.is_file() and target.stat().st_size>1024:
                            size=target.stat().st_size
                        else:
                            size=download_image(url,target)
                        item.update({'Status':'downloaded','Filename':filename,'Bytes':str(size),'Image URL':url})
                        done+=1
            except Exception as e:  # Keep processing after an individual artwork fails.
                item['Status']='error'; item['Error']=str(e)[:250]
            records[oid]=item
            save_manifest(manifest,records)
            print(f'[{n}/{len(pending)}] {oid}: {item["Status"]}')
            if n%args.batch_size==0 and n<len(pending):
                print(f'[PAUSE] {args.pause}s after {n} records...')
                time.sleep(args.pause)
            elif n<len(pending):
                time.sleep(args.delay+random.uniform(0,0.4))
    except KeyboardInterrupt:
        print('\n[STOP] Interrupted. Manifest saved; rerun to resume.')
        return
    print(f'[DONE] Downloaded this run: {done}; manifest: {manifest}')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv',default='MetObjects.csv',help='Path to local MetObjects.csv')
    p.add_argument('--directory',default='Met_highlights',help='Archive directory')
    p.add_argument('--no-update',action='store_true',help='Skip GitHub freshness check')
    p.add_argument('--snapshot-only',action='store_true',help='Only generate dated CSV snapshot')
    p.add_argument('--batch-size',type=int,default=100)
    p.add_argument('--pause',type=float,default=60,help='Seconds between batches')
    p.add_argument('--delay',type=float,default=1.5,help='Seconds between artwork requests')
    p.add_argument('--limit',type=int,default=0,help='Maximum artwork records to process in this run')
    p.add_argument('--retry-missing',action='store_true',help='Recheck records without images')
    a=p.parse_args()
    if a.batch_size<1 or a.pause<0 or a.delay<0 or a.limit<0: p.error('Batch size must be positive; times and limit nonnegative')
    try: run(a)
    except Exception as e:
        print(f'[ERROR] {e}',file=sys.stderr); sys.exit(1)
