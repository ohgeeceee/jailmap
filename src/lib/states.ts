export const US_STATES = [
  { name: 'Alabama', abbrev: 'AL', fipsCode: '01' },
  { name: 'Alaska', abbrev: 'AK', fipsCode: '02' },
  { name: 'Arizona', abbrev: 'AZ', fipsCode: '04' },
  { name: 'Arkansas', abbrev: 'AR', fipsCode: '05' },
  { name: 'California', abbrev: 'CA', fipsCode: '06' },
  { name: 'Colorado', abbrev: 'CO', fipsCode: '08' },
  { name: 'Connecticut', abbrev: 'CT', fipsCode: '09' },
  { name: 'Delaware', abbrev: 'DE', fipsCode: '10' },
  { name: 'Florida', abbrev: 'FL', fipsCode: '12' },
  { name: 'Georgia', abbrev: 'GA', fipsCode: '13' },
  { name: 'Hawaii', abbrev: 'HI', fipsCode: '15' },
  { name: 'Idaho', abbrev: 'ID', fipsCode: '16' },
  { name: 'Illinois', abbrev: 'IL', fipsCode: '17' },
  { name: 'Indiana', abbrev: 'IN', fipsCode: '18' },
  { name: 'Iowa', abbrev: 'IA', fipsCode: '19' },
  { name: 'Kansas', abbrev: 'KS', fipsCode: '20' },
  { name: 'Kentucky', abbrev: 'KY', fipsCode: '21' },
  { name: 'Louisiana', abbrev: 'LA', fipsCode: '22' },
  { name: 'Maine', abbrev: 'ME', fipsCode: '23' },
  { name: 'Maryland', abbrev: 'MD', fipsCode: '24' },
  { name: 'Massachusetts', abbrev: 'MA', fipsCode: '25' },
  { name: 'Michigan', abbrev: 'MI', fipsCode: '26' },
  { name: 'Minnesota', abbrev: 'MN', fipsCode: '27' },
  { name: 'Mississippi', abbrev: 'MS', fipsCode: '28' },
  { name: 'Missouri', abbrev: 'MO', fipsCode: '29' },
  { name: 'Montana', abbrev: 'MT', fipsCode: '30' },
  { name: 'Nebraska', abbrev: 'NE', fipsCode: '31' },
  { name: 'Nevada', abbrev: 'NV', fipsCode: '32' },
  { name: 'New Hampshire', abbrev: 'NH', fipsCode: '33' },
  { name: 'New Jersey', abbrev: 'NJ', fipsCode: '34' },
  { name: 'New Mexico', abbrev: 'NM', fipsCode: '35' },
  { name: 'New York', abbrev: 'NY', fipsCode: '36' },
  { name: 'North Carolina', abbrev: 'NC', fipsCode: '37' },
  { name: 'North Dakota', abbrev: 'ND', fipsCode: '38' },
  { name: 'Ohio', abbrev: 'OH', fipsCode: '39' },
  { name: 'Oklahoma', abbrev: 'OK', fipsCode: '40' },
  { name: 'Oregon', abbrev: 'OR', fipsCode: '41' },
  { name: 'Pennsylvania', abbrev: 'PA', fipsCode: '42' },
  { name: 'Rhode Island', abbrev: 'RI', fipsCode: '44' },
  { name: 'South Carolina', abbrev: 'SC', fipsCode: '45' },
  { name: 'South Dakota', abbrev: 'SD', fipsCode: '46' },
  { name: 'Tennessee', abbrev: 'TN', fipsCode: '47' },
  { name: 'Texas', abbrev: 'TX', fipsCode: '48' },
  { name: 'Utah', abbrev: 'UT', fipsCode: '49' },
  { name: 'Vermont', abbrev: 'VT', fipsCode: '50' },
  { name: 'Virginia', abbrev: 'VA', fipsCode: '51' },
  { name: 'Washington', abbrev: 'WA', fipsCode: '53' },
  { name: 'West Virginia', abbrev: 'WV', fipsCode: '54' },
  { name: 'Wisconsin', abbrev: 'WI', fipsCode: '55' },
  { name: 'Wyoming', abbrev: 'WY', fipsCode: '56' },
  { name: 'District of Columbia', abbrev: 'DC', fipsCode: '11' },
]

export const STATE_ABBREV_TO_NAME: Record<string, string> = US_STATES.reduce((acc, state) => {
  acc[state.abbrev] = state.name
  return acc
}, {} as Record<string, string>)

export const STATE_NAME_TO_ABBREV: Record<string, string> = US_STATES.reduce((acc, state) => {
  acc[state.name] = state.abbrev
  return acc
}, {} as Record<string, string>)

export function getStateByAbbrev(abbrev: string) {
  return US_STATES.find(s => s.abbrev.toLowerCase() === abbrev.toLowerCase())
}

export function getStateByName(name: string) {
  return US_STATES.find(s => s.name.toLowerCase() === name.toLowerCase())
}