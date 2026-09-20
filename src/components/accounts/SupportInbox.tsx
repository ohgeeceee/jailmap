'use client'

import { useCallback, useEffect, useState } from 'react'
import { CheckCircle2, Inbox, Mail, RefreshCw, Send } from 'lucide-react'

type Ticket = { id: string; name: string; email: string; subject: string; message: string; status: 'open' | 'closed'; created_at: number }
type Email = { uid: number; messageId: string; from: { name: string; address: string }; subject: string; receivedAt: string; text: string; seen: boolean }
async function getJson(url: string) { const response = await fetch(url); const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Inbox request failed.'); return result }

export function SupportInbox() {
  const [tickets, setTickets] = useState<Ticket[]>([]), [emails, setEmails] = useState<Email[]>([])
  const [configured, setConfigured] = useState(true), [view, setView] = useState<'tickets' | 'email'>('tickets')
  const [selected, setSelected] = useState<Ticket | Email | null>(null), [loading, setLoading] = useState(true), [busy, setBusy] = useState(false), [notice, setNotice] = useState('')
  const load = useCallback(async () => { setLoading(true); setNotice(''); try { if (view === 'tickets') setTickets((await getJson('/api/admin/inbox')).tickets); else { const result = await getJson('/api/admin/inbox?view=email'); setConfigured(result.configured); setEmails(result.messages) } } catch (error) { setNotice(error instanceof Error ? error.message : 'Inbox unavailable.') } finally { setLoading(false) } }, [view])
  useEffect(() => {
    let active = true
    const request = view === 'tickets' ? getJson('/api/admin/inbox') : getJson('/api/admin/inbox?view=email')
    request.then(result => {
      if (!active) return
      if (view === 'tickets') setTickets(result.tickets)
      else { setConfigured(result.configured); setEmails(result.messages) }
    }).catch(error => { if (active) setNotice(error instanceof Error ? error.message : 'Inbox unavailable.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [view])
  const isTicket = selected && 'created_at' in selected
  const recipient = selected ? (isTicket ? selected.email : selected.from.address) : ''
  const subject = selected ? `Re: ${selected.subject.replace(/^Re:\s*/i, '')}` : ''
  const items = view === 'tickets' ? tickets : emails
  return <section className="panel support-inbox">
    <div className="panel-heading"><div><h2>Support inbox</h2><p>Website tickets and email for getjailmap@gmail.com. Replies are sent from the configured support mailbox.</p></div><button className="jm-button secondary compact" onClick={() => void load()} disabled={loading}><RefreshCw size={15} />Refresh</button></div>
    <div className="inbox-tabs" role="tablist" aria-label="Inbox source"><button role="tab" aria-selected={view === 'tickets'} onClick={() => { setLoading(true); setView('tickets'); setSelected(null) }}><Inbox size={16} />Tickets</button><button role="tab" aria-selected={view === 'email'} onClick={() => { setLoading(true); setView('email'); setSelected(null) }}><Mail size={16} />Email</button></div>
    {notice && <p className="form-error" role="status">{notice}</p>}
    {loading ? <p className="panel-content" role="status">Loading inbox…</p> : view === 'email' && !configured ? <div className="empty-state"><Mail size={28} /><h3>Connect the support mailbox</h3><p>Add the Gmail app password to the server environment, then refresh this page.</p></div> : <div className="inbox-layout">
      <div className="inbox-list" aria-label={view === 'tickets' ? 'Support tickets' : 'Email messages'}>{items.map(item => { const ticket = 'created_at' in item; const active = selected && (ticket ? 'created_at' in selected && selected.id === item.id : !('created_at' in selected) && selected.uid === item.uid); return <button className={`inbox-row ${active ? 'selected' : ''}`} key={ticket ? item.id : item.uid} onClick={() => setSelected(item)}><span><strong>{ticket ? item.name : item.from.name}</strong>{ticket && <em className={`status-badge ${item.status === 'closed' ? '' : 'warning'}`}>{item.status}</em>}</span><b>{item.subject}</b><small>{new Date(ticket ? item.created_at * 1000 : item.receivedAt).toLocaleString()}</small></button>})}{items.length === 0 && <div className="empty-state"><CheckCircle2 size={28} /><h3>Inbox clear</h3><p>No messages to show.</p></div>}</div>
      <div className="inbox-detail">{!selected ? <div className="empty-state"><Mail size={28} /><h3>Select a message</h3><p>Choose a ticket or email to read and reply.</p></div> : <><div className="message-header"><span className="eyebrow">FROM</span><h3>{isTicket ? selected.name : selected.from.name}</h3><a href={`mailto:${recipient}`}>{recipient}</a><h2>{selected.subject}</h2></div><div className="message-body">{(isTicket ? selected.message : selected.text) || '(No plain-text message body)'}</div><form className="reply-form" onSubmit={async event => { event.preventDefault(); setBusy(true); setNotice(''); const form = event.currentTarget; const values = Object.fromEntries(new FormData(form)) as Record<string, string>; try { const response = await fetch('/api/admin/inbox', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ action: 'reply', to: recipient, subject: values.subject, message: values.message, ticketId: isTicket ? selected.id : undefined, inReplyTo: !isTicket ? selected.messageId : undefined, closeTicket: isTicket && values.closeTicket === 'on' }) }); const result = await response.json(); if (!response.ok) throw new Error(result.error || 'Reply failed.'); form.reset(); setNotice('Reply sent.'); if (isTicket && values.closeTicket === 'on') { setSelected(null); await load() } } catch (error) { setNotice(error instanceof Error ? error.message : 'Reply failed.') } finally { setBusy(false) } }}><label>Subject<input name="subject" defaultValue={subject} key={subject} maxLength={200} required /></label><label>Reply<textarea name="message" rows={7} maxLength={10000} required /></label><div className="reply-actions">{isTicket && <label className="check-label"><input name="closeTicket" type="checkbox" defaultChecked />Close ticket after sending</label>}<button className="jm-button" disabled={busy}>{busy ? 'Sending…' : <>Send reply <Send size={15} /></>}</button></div></form></> }</div>
    </div>}
  </section>
}
