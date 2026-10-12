import { useEffect, useState } from 'react'
import { CheckCircle2, CircleDollarSign, LoaderCircle, Play, RefreshCw, ShieldCheck, WalletCards } from 'lucide-react'
import './App.css'

const API = import.meta.env.VITE_API_BASE_URL ?? '/api'
type Ticket = { id: number; subject: string; requester: string; status: string; is_open: boolean; is_resolved: boolean }
type Event = { timestamp: string; agent: string; action: string; task: string; outcome: string; tool_name?: string }
type Payment = { payment?: { amount: number; kind: string } }
const labels: Record<string, string> = { boss: 'Boss', inventory: 'Inventory', accounting: 'Accounting', facilities: 'Facilities', customer_service: 'Customer Service' }

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(API + path, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: 'Request failed.' }))
    throw new Error(body.detail ?? 'Request failed.')
  }
  return response.json() as Promise<T>
}

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [cash, setCash] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState(101)
  const [payment, setPayment] = useState<Payment | null>(null)
  const [running, setRunning] = useState(false)
  const [approving, setApproving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const selected = tickets.find((ticket) => ticket.id === selectedId)

  async function refresh() {
    try {
      const [ticketData, eventData, balance] = await Promise.all([
        request<Ticket[]>('/tickets'), request<Event[]>('/events?limit=80'), request<{ balance: number }>('/cash/checking'),
      ])
      setTickets(ticketData); setEvents(eventData); setCash(balance.balance); setError('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to refresh dashboard.') }
  }
  async function refreshPayment(ticketId: number) {
    try {
      const prepared = await request<Payment>('/tickets/' + ticketId + '/payment-preparation')
      if (ticketId === selectedId) setPayment(prepared)
    } catch {
      if (ticketId === selectedId) setPayment(null)
    }
  }
  useEffect(() => { void refresh(); const timer = window.setInterval(() => void refresh(), 12000); return () => window.clearInterval(timer) }, [])
  useEffect(() => {
    let active = true
    setPayment(null)
    void request<Payment>('/tickets/' + selectedId + '/payment-preparation')
      .then((prepared) => { if (active) setPayment(prepared) })
      .catch(() => { if (active) setPayment(null) })
    return () => { active = false }
  }, [selectedId])
  async function runTeam() {
    if (!selected) return
    setRunning(true); setError(''); setMessage('')
    try {
      await request('/tickets/' + selected.id + '/run', { method: 'POST', body: JSON.stringify({ ticket_id: selected.id, request: 'Coordinate the next approved action for ' + selected.subject + '.' }) })
      const prepared = await request<Payment>('/tickets/' + selected.id + '/payment-preparation')
      setPayment(prepared)
      if (prepared.payment) {
        setMessage('Ticket ' + selected.id + ' is waiting for human payment approval.')
      } else {
        setMessage('Team analysis is recorded. A human must review any remaining blockers before resolving this ticket.')
      }
      await refresh()
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'The team did not complete the ticket.'); await refresh() }
    finally { setRunning(false) }
  }
  async function approvePayment() {
    if (!selected || !payment?.payment) return
    setApproving(true); setError('')
    try {
      await request('/tickets/' + selected.id + '/approve-payment', { method: 'POST', body: JSON.stringify({ approved_by: 'Dashboard human approval' }) })
      await request('/tickets/' + selected.id + '/resolve', { method: 'POST', body: JSON.stringify({ approved_by: 'Dashboard human approval' }) })
      await Promise.all([refresh(), refreshPayment(selected.id)]); setMessage('Payment approved and ticket ' + selected.id + ' marked resolved.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Approval failed.') }
    finally { setApproving(false) }
  }
  const ticketEvents = events.filter((event) => event.task.toLowerCase().includes('ticket ' + selectedId))
  const displayEvents = (ticketEvents.length ? ticketEvents : events).slice(-9).reverse()
  return (
    <main className="desk">
      <header className="masthead">
        <div><p className="kicker">Campus Customs / Operations</p><h1>Agent Desk</h1></div>
        <div className="header-actions"><div className="cash"><WalletCards size={18} /><span>Checking</span><strong>{cash === null ? '...' : '$' + cash.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong></div><button className="icon-button" onClick={() => void refresh()} title="Refresh"><RefreshCw size={18} /></button></div>
      </header>
      <section className="dashboard">
        <aside className="rail">
          <div className="rail-title"><div><p className="kicker">Live queue</p><h2>Tickets</h2></div><span>{tickets.filter((ticket) => ticket.is_open).length} open</span></div>
          <div className="ticket-stack">
            {tickets.map((ticket) => (
              <button className={'ticket ' + (ticket.id === selectedId ? 'selected' : '')} onClick={() => setSelectedId(ticket.id)} key={ticket.id}>
                <i className={ticket.is_resolved ? 'resolved' : ''} /><small>#{ticket.id}</small><strong>{ticket.subject}</strong><em>{ticket.status}</em>
              </button>
            ))}
          </div>
        </aside>
        <section className="workspace">
          <div className="ticket-header"><div><p className="kicker">Selected ticket</p><h2>{selected ? '#' + selected.id + ' ' + selected.subject : 'Loading...'}</h2><p className="requester">Requested by {selected?.requester}</p></div><div className="controls">{selected?.is_resolved && <span className="resolved"><CheckCircle2 size={16} /> Resolved</span>}<button className="run" disabled={!selected || selected.is_resolved || running} onClick={() => void runTeam()}>{running ? <LoaderCircle className="spin" size={17} /> : <Play size={17} fill="currentColor" />}{running ? 'Team running' : 'Run agent team'}</button></div></div>
          {message && <p className="notice good"><CheckCircle2 size={16} /> {message}</p>}
          {error && <p className="notice bad"><ShieldCheck size={16} /> {error}</p>}
          <section className="relay"><header><div><p className="kicker">Agent relay</p><h3>Work in motion</h3></div><span>Live refresh</span></header><div className="events">
            {displayEvents.length === 0 ? <p className="empty">Run the team to start this ticket's record.</p> : displayEvents.map((event, index) => <article className="event" key={event.timestamp + '-' + index}><b className={event.agent}>{labels[event.agent]?.[0] ?? 'A'}</b><div><strong>{labels[event.agent] ?? event.agent}</strong><span>{event.action.replaceAll('_', ' ')}</span><p>{event.tool_name ? 'Used ' + event.tool_name : event.outcome}</p></div><time>{new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time></article>)}
          </div></section>
          <div className="lower-grid">
            <section className="summary"><h3>Agent summary</h3>{Object.entries(labels).map(([role, label]) => { const event = ticketEvents.slice().reverse().find((item) => item.agent === role); return <div className="summary-row" key={role}><i className={role} /><strong>{label}</strong><span>{event?.outcome ?? 'Awaiting this ticket.'}</span></div> })}</section>
            <section className="approval"><h3><CircleDollarSign size={18} /> Human approval</h3>{payment?.payment ? <><p>Prepared {payment.payment.kind.replaceAll('_', ' ')} awaiting a human decision.</p><strong className="amount">${payment.payment.amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</strong><button onClick={() => void approvePayment()} disabled={approving}>{approving ? <LoaderCircle className="spin" size={17} /> : <CheckCircle2 size={17} />}{approving ? 'Approving' : 'Approve payment'}</button></> : <p className="no-payment">No payment awaits approval for this ticket.</p>}</section>
          </div>
        </section>
      </section>
    </main>
  )
}