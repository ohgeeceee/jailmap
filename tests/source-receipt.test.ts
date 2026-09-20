import { test } from 'node:test'
import assert from 'node:assert/strict'
import { canonicalPublicRecord, observationAge, receiptCompleteness } from '../src/lib/records/source-receipt.ts'
import type { Booking } from '../src/components/records/types.ts'

const booking: Booking = {
  id: 'synthetic', first_name: 'Example', last_name: 'Person', booking_number: 'EX-1',
  booking_date: '2026-09-20T00:00:00Z', observed_at: '2026-09-20T10:00:00Z',
  state: 'MT', county: 'Example', facility_name: 'Example Facility', source_url: 'https://example.gov/record',
  charges: [{ description: 'Synthetic charge', statute: null, severity: null }], bonds: [],
}

test('canonical receipt ignores ordering-only changes and observation time', () => {
  const second = { ...booking, observed_at: '2026-09-20T11:00:00Z', charges: [
    { description: 'Second', statute: '2', severity: null }, ...booking.charges,
  ] }
  const reordered = { ...second, charges: [...second.charges].reverse() }
  assert.equal(canonicalPublicRecord(second), canonicalPublicRecord(reordered))
  assert.equal(canonicalPublicRecord(booking), canonicalPublicRecord({ ...booking, observed_at: '2027-01-01T00:00:00Z' }))
})

test('receipt language distinguishes missing source categories', () => {
  assert.deepEqual(receiptCompleteness(booking), { charges: 'supplied', bonds: 'not supplied', statutes: 'partial' })
  assert.equal(observationAge(booking.observed_at, new Date('2026-09-20T12:00:00Z').getTime()), 'Observed 2 hours ago')
})
