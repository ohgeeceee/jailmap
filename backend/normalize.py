"""Contract for an authorized full booking record (charges/bonds are complete lists)."""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation

def required(value, field, maximum=200):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f'Invalid {field}')
    return value.strip()

def timestamp(value):
    result = datetime.fromisoformat(required(value, 'timestamp').replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamp requires timezone')
    if result > datetime.now(timezone.utc):
        raise ValueError('Future source timestamp')
    return result

def normalize(row):
    if row.get('status') not in ('in_custody', 'released'):
        raise ValueError('Explicit custody status required')
    result = {key: required(row.get(key), key) for key in ('booking_number','first_name','last_name')}
    result['booking_date'] = timestamp(row.get('booking_date'))
    result['source_updated_at'] = timestamp(row.get('source_updated_at'))
    result['dob'] = date.fromisoformat(row.get('dob')) if row.get('dob') else None
    if result['dob'] and result['dob'] > result['booking_date'].date():
        raise ValueError('DOB after booking')
    result['mugshot_url'] = row.get('mugshot_url')
    if result['mugshot_url'] and not result['mugshot_url'].startswith('https://'):
        raise ValueError('Image URL must use HTTPS')
    result['visibility'] = 'public' if row.get('status') == 'in_custody' else 'released'
    for collection in ('charges', 'bonds'):
        items = row.get(collection)
        if not isinstance(items, list) or len(items) > 200:
            raise ValueError(f'Complete {collection} list required')
        seen = set()
        result[collection] = []
        for item in items:
            source_id = required(item.get('source_id'), 'child id')
            if source_id in seen:
                raise ValueError('Duplicate child id')
            seen.add(source_id)
            if collection == 'charges':
                result[collection].append({'source_id': source_id,
                    'description': required(item.get('description'), 'description', 2000),
                    'statute': item.get('statute'), 'severity': item.get('severity')})
            else:
                try:
                    amount = Decimal(str(item['amount'])) if item.get('amount') is not None else None
                except InvalidOperation:
                    raise ValueError('Invalid amount') from None
                if amount is not None and (not amount.is_finite() or amount < 0 or amount > Decimal('999999999999.99')
                                            or amount.as_tuple().exponent < -2):
                    raise ValueError('Invalid USD amount')
                result[collection].append({'source_id': source_id, 'amount': amount,
                    'type': required(item.get('type'), 'bond type'),
                    'status': required(item.get('status'), 'bond status')})
    return result
