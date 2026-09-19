import { useCallback, useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowUpRight, AlertTriangle, CheckCircle2, Clock, Wrench, Archive, Loader2, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'
import { mockIncidents, type Incident as MockIncident } from '../data/mockData'
import { listIncidents, updateIncidentStatus, type IncidentRecord } from '../lib/api'
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts'

const severityColors: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#22c55e',
}

const pieColors = ['#ef4444', '#f97316', '#eab308', '#22c55e']

function normSeverity(s?: string): string {
  const v = (s ?? '').toLowerCase()
  return ['critical', 'high', 'medium', 'low'].includes(v) ? v : 'medium'
}

interface Row {
  id: string
  category: string
  location: string
  severity: string
  status: string
}

function toRow(rec: IncidentRecord): Row {
  return {
    id: rec.incident_id,
    category: rec.category ?? rec.analysis?.category ?? '—',
    location: rec.location || '—',
    severity: normSeverity(rec.severity ?? rec.analysis?.severity),
    status: rec.status ?? 'Open',
  }
}

function mockToRow(m: MockIncident): Row {
  const statusMap: Record<string, string> = {
    open: 'Open',
    assigned: 'Assigned',
    'in-progress': 'In Progress',
    resolved: 'Resolved',
    closed: 'Closed',
  }
  return { id: m.id, category: m.category, location: m.location, severity: m.severity, status: statusMap[m.status] ?? m.status }
}

const STATUS_META = [
  { label: 'Open', icon: AlertTriangle, color: 'text-rose-400' },
  { label: 'Assigned', icon: Clock, color: 'text-amber-400' },
  { label: 'In Progress', icon: Wrench, color: 'text-blue-400' },
  { label: 'Resolved', icon: CheckCircle2, color: 'text-emerald-400' },
  { label: 'Closed', icon: Archive, color: 'text-slate-400' },
]

export default function Dashboard() {
  const [rows, setRows] = useState<Row[]>([])
  const [live, setLive] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)
  const [closingId, setClosingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const incidents = await listIncidents()
      setRows([...incidents].reverse().map(toRow))
      setLive(true)
    } catch {
      setRows(mockIncidents.map(mockToRow))
      setLive(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const closeIssue = async (id: string) => {
    setClosingId(id)
    try {
      await updateIncidentStatus(id, 'Closed', 'Closed from operations dashboard')
      await load()
    } catch {
      // keep table as-is on failure; admin can retry from details page
    } finally {
      setClosingId(null)
    }
  }

  const stats = useMemo(
    () =>
      STATUS_META.map((s) => ({
        ...s,
        value: rows.filter((r) => r.status === s.label).length,
      })),
    [rows],
  )

  const severityData = useMemo(() => {
    const counts: Record<string, number> = { Critical: 0, High: 0, Medium: 0, Low: 0 }
    for (const r of rows) {
      const key = r.severity.charAt(0).toUpperCase() + r.severity.slice(1)
      if (key in counts) counts[key] += 1
    }
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [rows])

  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12 space-y-12">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">Operations Center</h1>
          <p className="text-slate-400">
            Real-time incident triage, AI assessments, and maintenance status.
            {live === false && <span className="text-amber-300"> Backend offline — showing sample data.</span>}
            {live === true && <span className="text-emerald-300"> Live from AI backend ({rows.length} incidents).</span>}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={load}
            disabled={loading}
            className="rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10 disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <Link
            to="/report"
            className="rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-bold text-[#030303] hover:bg-amber-300 shadow-lg shadow-amber-400/20"
          >
            + Report Incident
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {stats.map((s) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm hover:bg-white/10 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <s.icon className={`h-5 w-5 ${s.color}`} />
              <span className="text-xs text-slate-400 uppercase tracking-wider">{s.label}</span>
            </div>
            <div className="text-3xl font-extrabold text-white">{loading ? '…' : s.value}</div>
          </motion.div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-[#0a0a0a] p-6 shadow-xl shadow-black/40">
          <h2 className="text-xl font-bold text-white mb-6">Incident Trends — 7 Days</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={[
                  { day: 'Mon', count: 3 },
                  { day: 'Tue', count: 5 },
                  { day: 'Wed', count: 4 },
                  { day: 'Thu', count: 7 },
                  { day: 'Fri', count: 2 },
                  { day: 'Sat', count: 6 },
                  { day: 'Sun', count: 4 },
                ]}
              >
                <XAxis dataKey="day" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={{ stroke: '#334155' }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={{ stroke: '#334155' }} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#334155', borderRadius: 8, color: '#fff' }} />
                <Bar dataKey="count" fill="#fbbf24" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-6 shadow-xl shadow-black/40">
          <h2 className="text-xl font-bold text-white mb-6">Severity Distribution</h2>
          <div className="h-60 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={severityData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value" stroke="none">
                  {severityData.map((_, i) => (
                    <Cell key={i} fill={pieColors[i]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#334155', borderRadius: 8, color: '#fff' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-2 mt-4">
            {severityData.map((d, i) => (
              <span key={d.name} className="flex items-center gap-1.5 text-xs text-slate-300">
                <span className="h-2 w-2 rounded-full" style={{ backgroundColor: pieColors[i] }} /> {d.name} ({d.value})
              </span>
            ))}
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-white mb-4">Recent Incidents</h2>
        <div className="rounded-2xl border border-white/10 overflow-hidden bg-[#0a0a0a] shadow-xl shadow-black/40">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-slate-300 text-xs uppercase tracking-wider">
              <tr>
                <th className="text-left px-6 py-3 font-semibold">ID</th>
                <th className="text-left px-6 py-3">Category</th>
                <th className="text-left px-6 py-3">Location</th>
                <th className="text-left px-6 py-3">Severity</th>
                <th className="text-left px-6 py-3">Status</th>
                <th className="text-right px-6 py-3">Admin</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr className="border-t border-white/5">
                  <td colSpan={6} className="px-6 py-6 text-center text-slate-400">
                    <Loader2 className="inline h-4 w-4 animate-spin mr-2" /> Loading incidents…
                  </td>
                </tr>
              )}
              {!loading &&
                rows.slice(0, 8).map((i) => (
                  <tr key={i.id} className="border-t border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-6 py-3 font-mono text-xs text-slate-400">{i.id}</td>
                    <td className="px-6 py-3 text-white font-medium">{i.category}</td>
                    <td className="px-6 py-3 text-slate-300">{i.location}</td>
                    <td className="px-6 py-3">
                      <span
                        className="inline-block px-2 py-0.5 rounded-full text-xs font-bold capitalize"
                        style={{ backgroundColor: (severityColors[i.severity] ?? '#94a3b8') + '20', color: severityColors[i.severity] ?? '#94a3b8' }}
                      >
                        {i.severity}
                      </span>
                    </td>
                    <td className="px-6 py-3">
                      <Link to={`/details/${i.id}`} className="text-amber-300 hover:text-amber-200 font-medium">
                        {i.status} <ArrowUpRight className="inline h-3 w-3" />
                      </Link>
                    </td>
                    <td className="px-6 py-3 text-right">
                      {i.status !== 'Closed' && live ? (
                        <button
                          onClick={() => closeIssue(i.id)}
                          disabled={closingId === i.id}
                          className="rounded-md border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300 hover:bg-white/10 hover:text-white disabled:opacity-50"
                        >
                          {closingId === i.id ? 'Closing…' : 'Close'}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-600">{i.status === 'Closed' ? 'Closed' : '—'}</span>
                      )}
                    </td>
                  </tr>
                ))}
              {!loading && rows.length === 0 && (
                <tr className="border-t border-white/5">
                  <td colSpan={6} className="px-6 py-6 text-center text-slate-400">
                    No incidents yet — <Link to="/report" className="text-amber-300">report the first one</Link>.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
