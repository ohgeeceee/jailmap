import 'server-only'

import { ImapFlow } from 'imapflow'
import { simpleParser } from 'mailparser'
import nodemailer from 'nodemailer'

export type InboxMessage = {
  uid: number
  messageId: string
  from: { name: string; address: string }
  subject: string
  receivedAt: string
  text: string
  seen: boolean
}

function credentials() {
  const user = process.env.SUPPORT_EMAIL_USER || process.env.SMTP_USER
  const pass = process.env.SUPPORT_EMAIL_APP_PASSWORD || process.env.SMTP_PASSWORD
  if (!user || !pass) throw new Error('Support email is not configured')
  return { user, pass }
}

export function supportEmailConfigured() {
  return Boolean((process.env.SUPPORT_EMAIL_USER || process.env.SMTP_USER) &&
    (process.env.SUPPORT_EMAIL_APP_PASSWORD || process.env.SMTP_PASSWORD))
}

export async function readInbox(): Promise<InboxMessage[]> {
  const auth = credentials()
  const client = new ImapFlow({
    host: process.env.SUPPORT_IMAP_HOST || 'imap.gmail.com',
    port: Number(process.env.SUPPORT_IMAP_PORT || 993),
    secure: true,
    auth,
    logger: false,
  })
  await client.connect()
  try {
    const lock = await client.getMailboxLock('INBOX')
    try {
      const total = client.mailbox && typeof client.mailbox !== 'boolean' ? client.mailbox.exists : 0
      if (!total) return []
      const start = Math.max(1, total - 49)
      const messages: InboxMessage[] = []
      for await (const item of client.fetch(`${start}:*`, { uid: true, source: true, flags: true }, { uid: false })) {
        if (!item.source) continue
        const parsed = await simpleParser(item.source)
        const sender = parsed.from?.value[0]
        messages.push({
          uid: item.uid,
          messageId: parsed.messageId || '',
          from: { name: sender?.name || sender?.address || 'Unknown sender', address: sender?.address || '' },
          subject: parsed.subject || '(No subject)',
          receivedAt: (parsed.date || new Date()).toISOString(),
          text: (parsed.text || '').trim().slice(0, 20000),
          seen: item.flags?.has('\\Seen') || false,
        })
      }
      return messages.sort((a, b) => b.receivedAt.localeCompare(a.receivedAt))
    } finally {
      lock.release()
    }
  } finally {
    await client.logout().catch(() => undefined)
  }
}

export async function sendSupportReply(input: { to: string; subject: string; message: string; inReplyTo?: string }) {
  const auth = credentials()
  const port = Number(process.env.SUPPORT_SMTP_PORT || process.env.SMTP_PORT || 465)
  const transport = nodemailer.createTransport({
    host: process.env.SUPPORT_SMTP_HOST || process.env.SMTP_HOST || 'smtp.gmail.com',
    port,
    secure: port === 465,
    auth,
  })
  await transport.sendMail({
    from: process.env.SUPPORT_MAIL_FROM || process.env.MAIL_FROM || auth.user,
    to: input.to,
    subject: input.subject,
    text: input.message,
    ...(input.inReplyTo ? { inReplyTo: input.inReplyTo, references: input.inReplyTo } : {}),
  })
}
