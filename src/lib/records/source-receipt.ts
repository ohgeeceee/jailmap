import type { Booking } from '@/components/records/types'

export type ReceiptCompleteness = {
  charges: 'supplied' | 'not supplied'
  bonds: 'supplied' | 'not supplied'
  statutes: 'complete' | 'partial' | 'not supplied'
}

export function canonicalPublicRecord(booking: Booking) {
  const charges = booking.charges.map(charge => ({
    description: charge.description,
    severity: charge.severity || null,
    statute: charge.statute || null,
  })).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)))
  const bonds = booking.bonds.map(bond => ({
    amount: bond.amount,
    currency: bond.currency,
    status: bond.status,
    type: bond.type,
  })).sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)))
  return JSON.stringify({
    booking_date: booking.booking_date,
    booking_number: booking.booking_number,
    charges,
    bonds,
    county: booking.county,
    facility_name: booking.facility_name,
    first_name: booking.first_name,
    last_name: booking.last_name,
    source_url: booking.source_url,
    state: booking.state,
  })
}

export function receiptCompleteness(booking: Booking): ReceiptCompleteness {
  const statutes = booking.charges.filter(charge => Boolean(charge.statute)).length
  return {
    charges: booking.charges.length ? 'supplied' : 'not supplied',
    bonds: booking.bonds.length ? 'supplied' : 'not supplied',
    statutes: !booking.charges.length ? 'not supplied' : statutes === booking.charges.length ? 'complete' : 'partial',
  }
}

export function observationAge(observedAt: string, currentTime = Date.now()) {
  const milliseconds = Math.max(0, currentTime - new Date(observedAt).getTime())
  const hours = Math.floor(milliseconds / 3_600_000)
  if (hours < 1) return 'Observed less than an hour ago'
  if (hours < 24) return `Observed ${hours} hour${hours === 1 ? '' : 's'} ago`
  const days = Math.floor(hours / 24)
  return `Observed ${days} day${days === 1 ? '' : 's'} ago`
}
