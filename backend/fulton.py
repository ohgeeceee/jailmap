"""Fulton County CC-BY 4.0 named public roster.

The feed has names, booking numbers and dates, but no age, precise facility,
charges or bonds. Publish only the limited source-provided roster contract.
"""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import httpx
from backend.normalize import normalize

HOST = 'sharefulton.fultoncountyga.gov'
DATASET = '3vfv-9mmr'
URL = f'https://{HOST}/resource/{DATASET}.json'
META = f'https://{HOST}/api/views/{DATASET}.json'
EASTERN = ZoneInfo('America/New_York')

def snapshot_time(updated, now=None):
    now = now or datetime.now(timezone.utc)
    modified = datetime.fromtimestamp(updated,timezone.utc)
    if modified > now or now-modified > timedelta(hours=36):
        raise ValueError('Fulton dataset is stale or future dated')
    # County metadata explicitly says previous evening, approximately 7:30pm.
    day = modified.astimezone(EASTERN).date()-timedelta(days=1)
    return datetime.combine(day,time(19,30),EASTERN).astimezone(timezone.utc)

def convert(row, observed):
    if not isinstance(row.get('name'),str) or row['name'].count(',') != 1:
        raise ValueError('Unexpected Fulton name format')
    last, first = (part.strip() for part in row['name'].split(',',1))
    booking_date = datetime.fromisoformat(row['bookingdate'])
    if booking_date.tzinfo is not None or booking_date.time()!=time(0):
        raise ValueError('Fulton date-only contract changed')
    booking_date = booking_date.replace(tzinfo=EASTERN)
    result = normalize({'first_name':first,'last_name':last,'booking_number':row['bookingnbr'],
        'booking_date':booking_date.isoformat(),'updated_at':observed.isoformat(),
        'status':'in_custody','charges':[],'bonds':[]})
    result['observed_at'] = observed
    result['booking_date_precision'] = 'date'
    result['publication_blockers'] = []
    result['eligibility_basis'] = 'official_named_public_roster'
    result['unavailable_fields'] = ['age','specific_facility','charges','bonds']
    result['booking_timezone'] = 'America/New_York'
    if booking_date > observed:
        result['publication_blockers'].append('booking_after_stated_snapshot')
    result['charges_provided'] = False
    result['bonds_provided'] = False
    return result

def fetch_public(source):
    if source.get('staging_only') or source.get('adapter')!='fulton_public_roster':
        raise ValueError('Invalid public Fulton source configuration')
    rows=fetch({**source,'staging_only':True})
    # This is an intentionally public named roster. Do not enrich it with DOB,
    # photos or demographic inference, or claim that an age was verified.
    # Redacted/juvenile placeholders and inconsistent dates are never published.
    import re
    accepted=[row for row in rows if not row['publication_blockers'] and not re.search(
        r'\b(juvenile|redacted|withheld|sealed|unknown)\b',row['first_name']+' '+row['last_name'],re.I)]
    if not accepted: raise ValueError('No eligible source records; refuse to hide the whole prior roster')
    print(f'Fulton public source: {len(accepted)} eligible roster entries; {len(rows)-len(accepted)} withheld')
    return accepted

def fetch(source):
    if source['source_url'] != URL or not source.get('staging_only'):
        raise ValueError('Fulton adapter requires the exact reviewed URL and staging-only mode')
    def get(client,url,params=None):
        with client.stream('GET',url,params=params) as response:
            response.raise_for_status()
            content=bytearray()
            for chunk in response.iter_bytes():
                content.extend(chunk)
                if len(content)>10_000_000: raise ValueError('Fulton page too large')
        import json
        return json.loads(content)
    with httpx.Client(timeout=30,follow_redirects=False,headers={'User-Agent':'JailMap/1.0 (+https://jailmap.com)'}) as client:
        before=get(client,META)['rowsUpdatedAt']
        observed=snapshot_time(before)
        count=int(get(client,URL,{'$select':'count(*)'})[0]['count'])
        if not 1<=count<=20_000: raise ValueError('Unexpected Fulton snapshot size')
        rows=[]
        for offset in range(0,count,500):
            page=get(client,URL,{'$limit':500,'$offset':offset,'$order':'bookingnbr'})
            if not isinstance(page,list): raise ValueError('Invalid Fulton page')
            rows.extend(convert(row,observed) for row in page)
        if get(client,META)['rowsUpdatedAt'] != before or len(rows)!=count:
            raise ValueError('Fulton snapshot changed while fetching')
        if len({row['booking_number'] for row in rows})!=count:
            raise ValueError('Duplicate Fulton booking key')
        return rows
