import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, MapPin, CheckCircle2, Loader2, AlertTriangle, Archive, RotateCcw } from 'lucide-react'
import { mockIncidents } from '../data/mockData'
import { getIncident, updateIncidentStatus, INCIDENT_STATUSES, type IncidentRecord } from '../lib/api'

const statusStyles: Record<string, string> = {
  Open: 'bg-rose-400/20 text-rose-300',
  Assigned: 'bg-amber-400/20 text-amber-300',
  'In Progress': 'bg-blue-400/20 text-blue-300',
  Resolved: 'bg-emerald-400/20 text-emerald-300',
  Closed: 'bg-white/10 text-slate-400',
}

export default function IncidentDetails() {
  const { id } = useParams()
  const [record, setRecord] = useState<IncidentRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [live, setLive] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const rec = await getIncident(id)
      setRecord(rec)
      setLive(true)
    } catch {
      setRecord(null)
      setLive(false)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  const setStatus = async (status: string) => {
    if (!id || !record || record.status === status) return
    setUpdating(true)
    setError(null)
    try {
      const updated = await updateIncidentStatus(id, status, `Status set to ${status} from incident page`)
      setRecord(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Status update failed.')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-4xl px-6 lg:px-8 py-24 text-center text-slate-400">
        <Loader2 className="inline h-5 w-5 animate-spin mr-2" /> Loading incident…
      </div>
    )
  }

  // Sample-data fallback for the built-in CF-2024-* demo ids (not stored in backend)
  if (!live || !record) {
    const incident = mockIncidents.find((i) => i.id === id) || mockIncidents[0]
    return (
      <div className="mx-auto max-w-4xl px-6 lg:px-8 py-12 space-y-8">
        <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
          <ArrowLeft className="h-4 w-4" /> Back to Dashboard
        </Link>
        <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-200">
          Sample record — report a new incident to get a live backend-tracked ticket with admin controls.
        </div>
        <div className="rounded-2xl overflow-hidden border border-white/10 bg-[#0a0a0a] shadow-2xl shadow-black/40">
          <div className="h-72 bg-gradient-to-br from-slate-800 to-slate-900 relative flex items-center justify-center">
            <div className="text-6xl font-extrabold text-white/10 tracking-tighter">{incident.category}</div>
            <div className="absolute top-4 right-4 rounded-full px-3 py-1 text-xs font-bold bg-red-500/20 text-red-400 capitalize">
              {incident.severity}
            </div>
          </div>
          <div className="p-8 space-y-6">
            <div className="flex items-center gap-3 text-xs font-bold tracking-widest uppercase text-slate-400">
              <span>{incident.id}</span>
              <span>•</span>
              <span className="text-amber-300">{incident.category}</span>
            </div>
            <h1 className="text-3xl font-extrabold text-white leading-tight">{incident.description}</h1>
            <div className="grid md:grid-cols-3 gap-4">
              <InfoBox label="Location" value={incident.location} />
              <InfoBox label="Status" value={incident.status} />
              <InfoBox label="Department" value={incident.department} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  const analysis = record.analysis ?? {}
  const closed = record.status === 'Closed'
  const dupMatches = analysis.duplicate?.matches ?? []

  return (
    <div className="mx-auto max-w-4xl px-6 lg:px-8 py-12 space-y-8">
      <Link to="/dashboard" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Back to Dashboard
      </Link>

      <div className="rounded-2xl overflow-hidden border border-white/10 bg-[#0a0a0a] shadow-2xl shadow-black/40">
        <div className="h-56 bg-gradient-to-br from-slate-800 to-slate-900 relative flex items-center justify-center">
          <div className="text-5xl font-extrabold text-white/10 tracking-tighter text-center px-6">
            {record.category ?? analysis.category ?? 'Incident'}
          </div>
          <div className="absolute top-4 right-4 rounded-full px-3 py-1 text-xs font-bold bg-red-500/20 text-red-400">
            {record.severity ?? analysis.severity ?? '—'}
          </div>
          <div className={`absolute top-4 left-4 rounded-full px-3 py-1 text-xs font-bold ${statusStyles[record.status ?? 'Open'] ?? 'bg-white/10 text-slate-300'}`}>
            {record.status ?? 'Open'}
          </div>
        </div>

        <div className="p-8 space-y-6">
          <div className="flex items-center gap-3 text-xs font-bold tracking-widest uppercase text-slate-400">
            <span className="font-mono">{record.incident_id}</span>
            <span>•</span>
            <span className="text-amber-300">{record.category ?? analysis.category ?? '—'}</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white leading-tight">{record.description || 'Untitled incident'}</h1>
          <div className="grid md:grid-cols-3 gap-4">
            <InfoBox label="Location" value={record.location || '—'} />
            <InfoBox label="Department" value={analysis.department ?? '—'} />
            <InfoBox label="Reported" value={record.created_at ? new Date(record.created_at).toLocaleString() : '—'} />
          </div>

          <div className="rounded-xl bg-white/[0.03] border border-white/5 p-5 space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wide">AI Assessment</h3>
            <div className="grid sm:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-slate-400">Confidence:</span>{' '}
                <span className="font-bold text-white">
                  {typeof analysis.confidence === 'number' ? `${Math.round(analysis.confidence * 100)}%` : '—'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Severity:</span>{' '}
                <span className="font-bold text-rose-400">{analysis.severity ?? '—'}</span>
              </div>
              <div>
                <span className="text-slate-400">Action:</span>{' '}
                <span className="font-bold text-amber-300">{analysis.action ? `${analysis.action.slice(0, 60)}${analysis.action.length > 60 ? '…' : ''}` : '—'}</span>
              </div>
            </div>
            {analysis.summary && <p className="text-sm text-slate-300">{analysis.summary}</p>}
            {analysis.duplicate?.is_duplicate && dupMatches.length > 0 && (
              <p className="text-sm text-amber-300">
                Possible duplicate of {dupMatches[0].incident_id}
                {dupMatches[0].location ? ` (${dupMatches[0].location})` : ''}
              </p>
            )}
          </div>

          {/* Admin controls */}
          <div className="rounded-xl border border-white/10 bg-white/[0.02] p-5 space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wide">Admin — Status Control</h3>
            <div className="flex flex-wrap gap-2">
              {INCIDENT_STATUSES.map((s) => {
                const isActive = record.status === s
                return (
                  <button
                    key={s}
                    onClick={() => setStatus(s)}
                    disabled={updating || isActive}
                    className={`rounded-full px-4 py-1.5 text-xs font-bold transition-colors disabled:cursor-default ${
                      isActive ? 'bg-amber-400 text-[#030303]' : 'border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white disabled:opacity-60'
                    }`}
                  >
                    {s}
                  </button>
                )
              })}
            </div>
            {error && (
              <p className="flex items-center gap-2 text-sm text-rose-300">
                <AlertTriangle className="h-4 w-4" /> {error}
              </p>
            )}
            <div className="flex flex-wrap gap-3 pt-1">
              {!closed ? (
                <button
                  onClick={() => setStatus('Closed')}
                  disabled={updating}
                  className="rounded-lg bg-emerald-400 px-5 py-2.5 text-sm font-bold text-[#030303] hover:bg-emerald-300 disabled:opacity-50 flex items-center gap-2"
                >
                  {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Archive className="h-4 w-4" />}
                  Close Issue
                </button>
              ) : (
                <button
                  onClick={() => setStatus('Open')}
                  disabled={updating}
                  className="rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10 disabled:opacity-50 flex items-center gap-2"
                >
                  {updating ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                  Reopen Issue
                </button>
              )}
              {updating && <span className="text-xs text-slate-400 self-center">Updating status…</span>}
              {record.status && !updating && (
                <span className="text-xs text-slate-500 self-center flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" /> Current: {record.status}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function InfoBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white/[0.03] border border-white/5 p-4">
      <div className="flex items-center gap-2 text-xs text-slate-400 font-bold uppercase">
        <MapPin className="h-3.5 w-3.5" /> {label}
      </div>
      <div className="text-white font-medium mt-1">{value}</div>
    </div>
  )
}
