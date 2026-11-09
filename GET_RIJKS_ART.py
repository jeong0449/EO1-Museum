#!/usr/bin/env python3
"""EO1-Museum Rijksmuseum Linked Art collector v0.4.1.

Requires: python -m pip install requests
Search API: creator, type, material, technique, creationDate, title,
description, aboutActor, objectNumber, imageAvailable. Year ranges and
creator substring filters apply to resolved Linked Art records. Dry-run never downloads images.
"""
import argparse
import csv
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import requests

SEARCH = 'https://data.rijksmuseum.nl/search/collection'
FIELDS = ['id', 'object_number', 'title', 'creator', 'date', 'year', 'type', 'medium',
          'image_url', 'rights', 'rights_status', 'record_url', 'status']
EN = 'http://vocab.getty.edu/aat/300388277'


def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk(v)


def notations(node):
    return [x.get('@value', '') for x in node.get('notation', [])
            if isinstance(x, dict) and x.get('@value')]


def prefer_en(node):
    entries = node.get('notation', [])
    for x in entries:
        if isinstance(x, dict) and x.get('@language') == 'en':
            return x.get('@value', '')
    return next(iter(notations(node)), '')


def title_of(record):
    names = [x for x in record.get('identified_by', []) if x.get('type') == 'Name' and x.get('content')]
    for x in names:
        if any(y.get('id') == EN for y in x.get('language', [])) and not any(
                'former title' in prefer_en(z).lower() for z in x.get('classified_as', [])):
            return x['content']
    return names[0]['content'] if names else ''


def object_number(record):
    for x in record.get('identified_by', []):
        if x.get('type') == 'Identifier' and x.get('content'):
            return x['content']
    return ''


def creator_of(record):
    for x in walk(record.get('produced_by', {})):
        if x.get('type') in ('Person', 'Group'):
            return prefer_en(x) or next((z.get('content', '') for z in x.get('identified_by', []) if z.get('content')), '')
    return ''


def year_of(record):
    span = record.get('produced_by', {}).get('timespan', {})
    date = next((x.get('content', '') for x in span.get('identified_by', []) if x.get('content')), '')
    if not date:
        date = span.get('begin_of_the_begin', '')[:10]
    match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', date)
    return date, int(match.group(1)) if match else None


def image_and_rights(record):
    """Use the rights on the *image's* DigitalObject, not unrelated text."""
    image_url = ''
    rights = []
    for subject in record.get('subject_of', []):
        carrier = subject.get('digitally_carried_by', [])
        for digital in carrier:
            for point in digital.get('access_point', []):
                url = point.get('id', '')
                if re.match(r'^https?://iiif\.micr\.io/[\w-]+/full/', url):
                    if not image_url:
                        image_url = url
                        for note in digital.get('referred_to_by', []):
                            rights.extend([note.get('content', ''), note.get('_label', '')])
    # Fallback for image links encoded as IIIF service rather than a full image URL.
    if not image_url:
        for node in walk(record.get('subject_of', [])):
            if node.get('type') == 'DigitalObject':
                url = node.get('id', '')
                m = re.match(r'^(https?://iiif\.micr\.io/[\w-]+)(?:/info\.json)?$', url)
                if m:
                    image_url = m.group(1) + '/full/max/0/default.jpg'
                    break
    for node in walk(record.get('subject_of', [])):
        if node.get('type') == 'Right':
            for cls in node.get('classified_as', []):
                rights.append(cls.get('id', ''))
    return image_url, ' | '.join(dict.fromkeys(x for x in rights if x))


def rights_status(rights):
    low = rights.lower()
    if 'creativecommons.org/publicdomain/' in low or 'creativecommons.org/publicdomain/zero' in low:
        return 'public_domain'
    if any(x in low for x in ('creativecommons.org/licenses/by', 'in copyright', 'all rights reserved')):
        return 'restricted_or_review'
    return 'unknown'


def make_row(record, uri):
    date, year = year_of(record)
    image, rights = image_and_rights(record)
    types = [prefer_en(x) for x in record.get('classified_as', [])]
    materials = [prefer_en(x) for x in record.get('made_of', [])]
    row = dict(id=uri.rstrip('/').split('/')[-1], object_number=object_number(record),
               title=title_of(record), creator=creator_of(record), date=date,
               year=year or '', type='; '.join(x for x in types if x),
               medium='; '.join(x for x in materials if x), image_url=image,
               rights=rights, rights_status=rights_status(rights),
               record_url=uri, status='candidate')
    return row


def request_json(session, url, params=None, retries=3):
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=(12, 50), headers={'Accept': 'application/json'})
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)


def get_identifiers(session, args):
    params = {'imageAvailable': 'true'}
    for key, value in [('creator', args.artist), ('type', args.type if args.type != 'all' else None),
                       ('material', args.material), ('technique', args.technique),
                       ('creationDate', args.creation_date), ('title', args.title),
                       ('description', args.description), ('aboutActor', args.about_actor),
                       ('objectNumber', args.object_number)]:
        if value:
            params[key] = value
    url, first, ids, total = SEARCH, True, [], None
    while url:
        page = request_json(session, url, params if first else None)
        first = False
        total = page.get('partOf', {}).get('totalItems', total)
        ids.extend(x['id'] for x in page.get('orderedItems', []) if x.get('id'))
        next_page = page.get('next')
        url = next_page.get('id') if isinstance(next_page, dict) else next_page if isinstance(next_page, str) else None
        print(f'  Search: {len(ids)} / {total if total is not None else "?"} identifiers', flush=True)
    return list(dict.fromkeys(ids)), total


def matches(row, args):
    if args.year_from is not None and (not row['year'] or row['year'] < args.year_from):
        return False
    if args.year_to is not None and (not row['year'] or row['year'] > args.year_to):
        return False
    for field, term in [('creator', args.creator_contains)]:
        if term and term.casefold() not in str(row[field]).casefold():
            return False
    return True


def save_csv(rows, path):
    # Direct writing avoids the previous Windows tmp -> CSV replace failure.
    # An open CSV in Excel can still block writing; report a helpful error.
    try:
        with path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    except PermissionError as exc:
        raise RuntimeError(f'Cannot write {path}; close it in Excel or Explorer preview: {exc}') from exc


def download(session, url, dest):
    part = dest.with_name(dest.name + '.part')
    try:
        with session.get(url, stream=True, timeout=(12, 120)) as response:
            response.raise_for_status()
            if 'image/' not in response.headers.get('Content-Type', '').lower():
                raise RuntimeError('Response is not an image')
            with part.open('wb') as stream:
                for chunk in response.iter_content(256 * 1024):
                    if chunk:
                        stream.write(chunk)
        if part.stat().st_size < 1024:
            raise RuntimeError('Image file too small')
        part.replace(dest)
    finally:
        part.unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description='Rijksmuseum collector v0.4.1')
    p.add_argument('--artist', help='Search API creator (optional; no default artist)')
    p.add_argument('--type', default='all', help='Search API object type, e.g. painting, print, drawing')
    p.add_argument('--title', help='Search API title keyword')
    p.add_argument('--material', help='Search API material, e.g. porcelain or silver')
    p.add_argument('--medium', help='Alias of --material (formerly a local filter)')
    p.add_argument('--technique', help='Search API technique, e.g. etching')
    p.add_argument('--creation-date', help='Search API creationDate pattern, e.g. 16?? for 1600-1699')
    p.add_argument('--century', type=int, help='Local year filter: 17 means 1600-1699 (not sent to API)')
    p.add_argument('--description', help='Search API description keyword')
    p.add_argument('--about-actor', help='Search API depicted person or group')
    p.add_argument('--creator-contains', help='Creator substring (local record filter)')
    p.add_argument('--object-number', help='Search API object number or wildcard')
    p.add_argument('--year-from', type=int, help='Minimum creation year (local record filter)')
    p.add_argument('--year-to', type=int, help='Maximum creation year (local record filter)')
    p.add_argument('--dry-run', action='store_true', help='Resolve and count rights; never download images')
    cache_group = p.add_mutually_exclusive_group()
    cache_group.add_argument('--refresh', action='store_true',
                             help='Re-fetch detailed records from API, replacing cached JSON')
    cache_group.add_argument('--cache-only', action='store_true',
                             help='Offline: inspect cached JSON only (not a complete collection count)')
    p.add_argument('--target', type=int, default=20, help='Images to obtain (default 20)')
    p.add_argument('--max-resolve', type=int, default=0, help='Max records to inspect, 0 = all')
    p.add_argument('--delay', type=float, default=0.5)
    p.add_argument('--original', type=Path, default=Path('original'))
    p.add_argument('--metadata-dir', type=Path, default=Path('Rijksmuseum'))
    p.add_argument('--allow-unknown-rights', action='store_true', help='Download unknown-rights images at your own risk')
    args = p.parse_args()
    if args.century is not None:
        if not 1 <= args.century <= 21:
            p.error('--century must be between 1 and 21')
        if args.creation_date:
            p.error('Use either --century or --creation-date, not both')
        century_start = (args.century - 1) * 100
        century_end = century_start + 99
        args.year_from = max(args.year_from, century_start) if args.year_from is not None else century_start
        args.year_to = min(args.year_to, century_end) if args.year_to is not None else century_end
    if args.medium and args.material and args.medium.casefold() != args.material.casefold():
        p.error('Use --material or --medium, not conflicting values')
    args.material = args.material or args.medium
    if not args.cache_only and not any((args.artist, args.type != 'all', args.material,
            args.technique, args.creation_date, args.title, args.description,
            args.about_actor, args.object_number)):
        p.error('Specify at least one API search filter; --century is a local filter and requires an API search condition')
    if min(args.target, args.max_resolve, args.delay) < 0:
        p.error('--target, --max-resolve, and --delay must be nonnegative')
    if args.year_from is not None and args.year_to is not None and args.year_from > args.year_to:
        p.error('--year-from cannot exceed --year-to')
    args.metadata_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = args.metadata_dir / 'records'
    cache_dir.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers.update({'User-Agent': 'EO1-Museum-Rijks/0.4.1 (personal art display)'})
    cache_mode = 'offline' if args.cache_only else ('refresh' if args.refresh else 'auto')
    print(f'Rijksmuseum: creator={args.artist or chr(45)}, type={args.type}, cache={cache_mode}, dry-run={args.dry_run}')
    if args.century is not None:
        print(f'  Local century filter: {args.year_from}–{args.year_to} (not sent to API)')
    if args.cache_only:
        ids = ['https://id.rijksmuseum.nl/' + f.stem for f in sorted(cache_dir.glob('*.json'))]
        total = None
        print(f'  Offline cache: {len(ids)} records (not a complete API search)')
    else:
        try:
            ids, total = get_identifiers(session, args)
        except Exception as exc:
            print(f'[ERROR] Search failed: {exc}', file=sys.stderr)
            return 1
    print(f'API search imageAvailable matches: {total if total is not None else "not checked"}; IDs: {len(ids)}')
    if args.max_resolve:
        ids = ids[:args.max_resolve]
    # Distinct output names avoid overwriting previous search reports.
    label_parts = [args.artist or 'any_artist', args.type]
    for name, val in [('title', args.title), ('material', args.material),
                      ('technique', args.technique), ('date', args.creation_date),
                      ('description', args.description), ('about', args.about_actor),
                      ('creator', args.creator_contains), ('number', args.object_number),
                      ('from', args.year_from), ('to', args.year_to)]:
        if val is not None:
            label_parts.extend([name, str(val)])
    label = re.sub(r'[^A-Za-z0-9_-]+', '_', '_'.join(label_parts)).strip('_')[:120] or 'collection'
    csv_path = args.metadata_dir / f'{label}_metadata.csv'
    json_path = args.metadata_dir / f'{label}_metadata.json'
    rows, errors = [], 0
    downloaded, cache_hits, checked, matched = 0, 0, 0, 0
    rights_counts = Counter()
    for index, uri in enumerate(ids, 1):
        rid = uri.rstrip('/').split('/')[-1]
        cache_file = cache_dir / f'{rid}.json'
        try:
            record = None
            if not args.refresh and cache_file.exists():
                try:
                    record = json.loads(cache_file.read_text(encoding='utf-8'))
                    if not isinstance(record, dict):
                        raise ValueError('Cached record is not a JSON object')
                    cache_hits += 1
                except (OSError, ValueError) as exc:
                    if args.cache_only:
                        raise RuntimeError(f'Invalid offline cache: {exc}') from exc
                    print(f'  [WARN] Bad cache {cache_file.name}; fetching again', flush=True)
            if record is None:
                if args.cache_only:
                    continue
                record = request_json(session, uri, {'_profile': 'la-framed'})
                tmp = cache_file.with_suffix('.json.tmp')
                tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
                tmp.replace(cache_file)
                time.sleep(args.delay)
            checked += 1
            row = make_row(record, uri)
            if not matches(row, args):
                continue
            matched += 1
            if not row['image_url']:
                row['status'] = 'no_image_url'
                rights_counts['no_image_url'] += 1
            else:
                rights_counts[row['rights_status']] += 1
                if row['rights_status'] != 'public_domain' and not (
                        args.allow_unknown_rights and row['rights_status'] == 'unknown'):
                    row['status'] = 'skipped_' + row['rights_status']
                elif not args.dry_run and downloaded < args.target:
                    dest = args.original / f'rijks_{rid}.jpg'
                    if dest.exists() and dest.stat().st_size > 1024:
                        row['status'] = 'already_exists'
                        downloaded += 1
                    else:
                        args.original.mkdir(parents=True, exist_ok=True)
                        try:
                            download(session, row['image_url'], dest)
                            row['status'] = 'downloaded'
                            downloaded += 1
                            time.sleep(args.delay)
                        except Exception as exc:
                            row['status'] = 'download_error: ' + str(exc)[:100]
            rows.append(row)
        except Exception as exc:
            errors += 1
            rows.append({**dict.fromkeys(FIELDS, ''), 'id': rid, 'record_url': uri,
                         'status': 'metadata_error: ' + str(exc)[:100]})
        finally:
            if index % 20 == 0 or index == len(ids):
                print(f'  Resolved {index}/{len(ids)}; filter matches {matched}; '
                      f'PD images {rights_counts["public_domain"]}; downloaded {downloaded}/{args.target}', flush=True)
        # Normal downloads stop once target reached; dry-run inspects all candidates.
        if not args.dry_run and downloaded >= args.target:
            break
    summary = {'artist': args.artist, 'type': args.type,
               'api_filters': {k: v for k, v in [('material', args.material), ('technique', args.technique),
                   ('creationDate', args.creation_date), ('title', args.title),
                   ('description', args.description), ('aboutActor', args.about_actor),
                   ('objectNumber', args.object_number)] if v},
               'image_available_search_total': total, 'search_identifiers': len(ids),
               'resolved': checked, 'filter_matches': matched, 'metadata_errors': errors,
               'rights_counts': dict(rights_counts), 'cache_hits': cache_hits,
               'dry_run': args.dry_run, 'generated_utc': datetime.now(timezone.utc).isoformat(),
               'records': rows}
    try:
        save_csv(rows, csv_path)
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    except (OSError, RuntimeError) as exc:
        print(f'[ERROR] Report saving failed: {exc}', file=sys.stderr)
        return 1
    print('\n--- Summary ---')
    print(f'API imageAvailable matches: {total if total is not None else "not checked (offline)"}')
    print(f'Detailed records checked: {checked} (cache hits: {cache_hits}; errors: {errors})')
    print(f'After local filters: {matched}')
    print(f'Public-domain image URLs: {rights_counts["public_domain"]}')
    print(f'Unknown rights: {rights_counts["unknown"]}; restricted/review: {rights_counts["restricted_or_review"]}')
    print(f'No image URL: {rights_counts["no_image_url"]}')
    print(f'Images obtained (including existing): {downloaded}')
    print('Cache policy: ' + ('offline only' if args.cache_only else
                              'forced refresh' if args.refresh else 'reuse existing, fetch missing'))
    if checked < len(ids):
        print('PARTIAL RESULT: Not all search identifiers were resolved.')
    if args.cache_only:
        print('OFFLINE RESULT: Counts apply only to locally cached JSON records.')
    print(f'Reports: {csv_path}, {json_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
