import { randomUUID } from 'node:crypto'
import { database, emailValue, textValue } from '../accounts/store.ts'

export type SupportTicket = {
  id: string
  name: string
  email: string
  subject: string
  message: string
  status: 'open' | 'closed'
  created_at: number
  updated_at: number
}

function supportDatabase() {
  const db = database()
  db.exec(`
    CREATE TABLE IF NOT EXISTS support_tickets (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT NOT NULL,
      subject TEXT NOT NULL,
      message TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','closed')),
      created_at INTEGER NOT NULL,
      updated_at INTEGER NOT NULL
    );
    CREATE INDEX IF NOT EXISTS support_ticket_status_date
      ON support_tickets(status, created_at DESC);
  `)
  return db
}

export function createSupportTicket(input: Record<string, unknown>) {
  const name = textValue(input.name, 'Name', 2, 80)
  const email = emailValue(input.email)
  const subject = textValue(input.subject, 'Subject', 3, 140)
  const message = textValue(input.message, 'Message', 10, 5000)
  const id = randomUUID()
  const createdAt = Math.floor(Date.now() / 1000)
  supportDatabase().prepare(`
    INSERT INTO support_tickets(id,name,email,subject,message,status,created_at,updated_at)
    VALUES (?,?,?,?,?,'open',?,?)
  `).run(id, name, email, subject, message, createdAt, createdAt)
  return id
}

export function listSupportTickets(status?: string) {
  const db = supportDatabase()
  const filter = status === 'closed' ? 'closed' : status === 'all' ? null : 'open'
  const rows = filter
    ? db.prepare('SELECT * FROM support_tickets WHERE status=? ORDER BY created_at DESC LIMIT 100').all(filter)
    : db.prepare('SELECT * FROM support_tickets ORDER BY created_at DESC LIMIT 100').all()
  return rows.map(row => ({ ...row })) as SupportTicket[]
}

export function getSupportTicket(id: string) {
  return supportDatabase().prepare('SELECT * FROM support_tickets WHERE id=?').get(id) as SupportTicket | undefined
}

export function setSupportTicketStatus(id: string, status: unknown) {
  if (status !== 'open' && status !== 'closed') throw new Error('Invalid ticket status')
  const result = supportDatabase().prepare('UPDATE support_tickets SET status=?,updated_at=? WHERE id=?')
    .run(status, Math.floor(Date.now() / 1000), id)
  if (!result.changes) throw new Error('Ticket not found')
}
