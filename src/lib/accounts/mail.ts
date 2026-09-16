import 'server-only'
import nodemailer from 'nodemailer'

let transport: ReturnType<typeof nodemailer.createTransport> | undefined
function mailer() {
  if (transport) return transport
  const host = process.env.SMTP_HOST
  const user = process.env.SMTP_USER
  const pass = process.env.SMTP_PASSWORD
  if (!host || !user || !pass) throw new Error('SMTP is not configured')
  const port = Number(process.env.SMTP_PORT || 587)
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