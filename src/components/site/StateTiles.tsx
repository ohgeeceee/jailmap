import Link from 'next/link'
const rows = [
  ['','','','','','','','','','','','ME'],
  ['','WA','ID','MT','ND','MN','','MI','','VT','NH',''],
  ['','OR','NV','WY','SD','IA','WI','OH','PA','NY','MA',''],
  ['','CA','UT','CO','NE','MO','IL','IN','WV','NJ','CT','RI'],
  ['','','AZ','NM','KS','AR','KY','TN','VA','MD','DE',''],
  ['','','','','OK','LA','MS','AL','GA','NC','',''],
  ['','AK','HI','','TX','','','','FL','SC','',''],
]
export function StateTiles() {
  return <div className="state-tiles" aria-label="Browse by state; availability varies by source">{rows.flatMap((row, y) => row.map((state, x) => state ? <Link href={`/search?state=${state}`} key={state} style={{ gridColumn: x + 1, gridRow: y + 1 }} title={`Search ${state}`} className={['MT','TX','CA','NY'].includes(state) ? 'tile-accent' : ''}>{state}</Link> : null))}</div>
}
