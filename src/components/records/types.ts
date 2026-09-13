export type Booking = {
  id: string; first_name: string; last_name: string; booking_number: string;
  booking_date: string; observed_at: string; state: string; county: string;
  booking_date_precision?: 'date' | 'timestamp'; booking_timezone?: string;
  source_note?: string | null;
  facility_name: string; source_url: string;
  charges: { statute: string | null; description: string; severity: string | null }[];
  bonds: { amount: number | null; currency: string; type: string; status: string }[];
}
export type Jurisdiction = { id: string; state: string; county: string; facility_name: string }
export function bondLabel(bond: Booking['bonds'][number]) {
  return `${bond.amount === null ? 'Amount unknown' : new Intl.NumberFormat('en-US', { style: 'currency', currency: bond.currency }).format(bond.amount)} · ${bond.type} · ${bond.status}`
}
