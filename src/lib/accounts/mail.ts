import nodemailer from 'nodemailer'

let transport: ReturnType<typeof nodemailer.createTransport> | undefined
function mailer() {
  if (transport) return transport
  const host = process.env.SMTP_HOST || process.env.SUPPORT_SMTP_HOST
  const user = process.env.SMTP_USER || process.env.SUPPORT_EMAIL_USER
  const pass = process.env.SMTP_PASSWORD || process.env.SUPPORT_EMAIL_APP_PASSWORD
  if (!host || !user || !pass) throw new Error('SMTP is not configured')
  const port = Number(process.env.SMTP_PORT || process.env.SUPPORT_SMTP_PORT || 587)
  transport = nodemailer.createTransport({ host, port, secure: port === 465, auth: { user, pass } })
  return transport
}

export async function sendPasswordResetEmail(to: string, link: string) {
  const from = process.env.MAIL_FROM || process.env.SMTP_USER!
  await mailer().sendMail({
    from,
    to,
    subject: 'Reset your JailMap password',
    text: `We received a request to reset your JailMap password.\n\nOpen this link to choose a new password (it expires in one hour):\n\n${link}\n\nIf you didn't request this, you can ignore this email and your password will stay the same.`,
    html: `<p>We received a request to reset your JailMap password.</p><p><a href="${link}">Choose a new password</a> — this link expires in one hour.</p><p>If you didn't request this, you can ignore this email and your password will stay the same.</p>`,
  })
}

export type WatchlistAlertBooking = {
  id: string
  first_name: string
  last_name: string
  county: string
  state: string
  facility_name?: string
  booking_date?: string
}

function escapeHtml(value: string) {
  return value.replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]!)
}

export async function sendWatchlistAlertEmail(input: {
  to: string
  accountName: string
  label: string
  query: string
  state: string
  county: string
  matches: WatchlistAlertBooking[]
  manageUrl: string
}) {
  const from = process.env.MAIL_FROM || process.env.SUPPORT_MAIL_FROM || process.env.SMTP_USER || process.env.SUPPORT_EMAIL_USER!
  const location = [input.county, input.state].filter(Boolean).join(', ') || 'all supported locations'
  const subject = `JailMap watchlist alert: ${input.label}`
  const lines = input.matches.slice(0, 10).map(match => {
    const name = `${match.first_name} ${match.last_name}`.trim()
    return `- ${name || 'Name unavailable'} — ${match.county}, ${match.state}${match.facility_name ? ` (${match.facility_name})` : ''}`
  })
  const text = `Hi ${input.accountName || 'there'},\n\nJailMap found ${input.matches.length} new matching public ${input.matches.length === 1 ? 'record' : 'records'} for your watchlist "${input.label}".\n\nSearch: ${input.query}\nLocation: ${location}\n\n${lines.join('\n')}\n\nManage this watchlist:\n${input.manageUrl}\n\nA name match is a starting point, not proof of identity. Confirm details with the original source.`
  const htmlItems = input.matches.slice(0, 10).map(match => {
    const name = escapeHtml(`${match.first_name} ${match.last_name}`.trim() || 'Name unavailable')
    const place = escapeHtml(`${match.county}, ${match.state}`)
    const facility = match.facility_name ? ` <span style="color:#65726b;">(${escapeHtml(match.facility_name)})</span>` : ''
    return `<li><strong>${name}</strong> — ${place}${facility}</li>`
  }).join('')
  const html = `<p>Hi ${escapeHtml(input.accountName || 'there')},</p>
    <p>JailMap found ${input.matches.length} new matching public ${input.matches.length === 1 ? 'record' : 'records'} for your watchlist <strong>${escapeHtml(input.label)}</strong>.</p>
    <p><strong>Search:</strong> ${escapeHtml(input.query)}<br /><strong>Location:</strong> ${escapeHtml(location)}</p>
    <ul>${htmlItems}</ul>
    <p><a href="${escapeHtml(input.manageUrl)}">Manage this watchlist</a></p>
    <p style="color:#65726b;font-size:12px;">A name match is a starting point, not proof of identity. Confirm details with the original source.</p>`
  await mailer().sendMail({ from, to: input.to, subject, text, html })
}
