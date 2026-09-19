import { useCallback, useEffect, useMemo, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { Loader2, RefreshCw } from 'lucide-react'
import { getInsights, listIncidents, type IncidentRecord, type Insight } from '../lib/api'

const FALLBACK_INSIGHTS: Insight[] = [
  { headline: 'Peak Risk Hours', detail: 'Traffic and electrical incidents peak 14:00–16:00 on weekdays.' },
  { headline: 'Recurring Zones', detail: 'Library roof and Engineering basement show repeat patterns.' },
  { headline: 'Category Shift', detail: 'Fire-safety reports increased 22% after inspection campaign.' },
  { headline: 'Resolution Speed', detail: 'AI-triaged tickets resolve 40% faster than manual intake.' },
]

const FALLBACK_CATEGORIES = [
  { name: 'Electrical', count: 12 },
  { name: 'Structural', count: 8 },
  { name: 'Fire', count: 5 },
  { name: 'Plumbing', count: 9 },
  { name: 'Environmental', count: 4 },
]

function dayKey(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export default function Analytics() {
  const [incidents, setIncidents] = useState<IncidentRecord[]>([])
  const [insights, setInsights] = useState<Insight[]>(FALLBACK_INSIGHTS)
  const [live, setLive] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [incs, ins] = await Promise.all([listIncidents(), getInsights()])
      setIncidents(incs)
      if (ins.length > 0) setInsights(ins)
      setLive(true)
    } catch {
      setLive(false)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const categoryData = useMemo(() => {
    if (!live || incidents.length === 0) return FALLBACK_CATEGORIES
    const counts = new Map<string, number>()
    for (const inc of incidents) {
      const cat = inc.category ?? inc.analysis?.category ?? 'Unknown'
      counts.set(cat, (counts.get(cat) ?? 0) + 1)
    }
    return [...counts.entries()]
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 8)
  }, [incidents, live])

  const weeklyData = useMemo(() => {
    const days: { key: string; label: string; r: number }[] = []
    const now = new Date()
    for (let i = 6; i >= 0; i--) {
      const d = new Date(now)
      d.setDate(now.getDate() - i)
      days.push({
        key: dayKey(d),
        label: d.toLocaleDateString(undefined, { weekday: 'short' }),
        r: 0,
      })
    }
    if (live) {
      for (const inc of incidents) {
        if (!inc.created_at) continue
        const k = dayKey(new Date(inc.created_at))
        const bucket = days.find((d) => d.key === k)
        if (bucket) bucket.r += 1
      }
    } else {
      const fallback = [2, 5, 3, 7, 4, 6, 5]
      days.forEach((d, i) => {
        d.r = fallback[i]
      })
    }
    return days.map(({ label, r }) => ({ d: label, r }))
  }, [incidents, live])

  const openCount = incidents.filter((i) => (i.status ?? 'Open') !== 'Closed').length
  const closedCount = incidents.filter((i) => i.status === 'Closed').length

  return (
    <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12 space-y-12">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">Analytics & Trends</h1>
          <p className="text-slate-400">
            Multi-dimensional analysis of incident patterns, categories, and AI predictions.
            {live === true && <span className="text-emerald-300"> Live from AI backend.</span>}
            {live === false && <span className="text-amber-300"> Backend offline — showing sample data.</span>}
          </p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium text-white hover:bg-white/10 disabled:opacity-50 flex items-center gap-2"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {live && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Total Incidents', value: incidents.length },
            { label: 'Open', value: openCount },
            { label: 'Closed', value: closedCount },
            { label: 'AI Insights', value: insights.length },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border border-white/10 bg-white/5 p-5">
              <div className="text-xs text-slate-400 uppercase tracking-wider mb-2">{s.label}</div>
              <div className="text-3xl font-extrabold text-white">{loading ? '…' : s.value}</div>
            </div>
          ))}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-6 shadow-xl shadow-black/40">
          <h2 className="text-xl font-bold text-white mb-4">Category Breakdown{live ? ' — Live' : ''}</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={categoryData}>
                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#334155', color: '#fff' }} />
                <Bar dataKey="count" fill="#fbbf24" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-6 shadow-xl shadow-black/40">
          <h2 className="text-xl font-bold text-white mb-4">Weekly Trend (Reports){live ? ' — Live' : ''}</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="d" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0a0a', borderColor: '#334155', color: '#fff' }} />
                <Area type="monotone" dataKey="r" stroke="#38bdf8" fill="#38bdf8" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-gradient-to-br from-amber-400/10 to-rose-500/10 p-8 shadow-2xl shadow-black/40">
        <h2 className="text-2xl font-extrabold text-white mb-2">AI Insights{live ? ' — Live' : ''}</h2>
        <p className="text-sm text-slate-300 mb-4">
          {live ? 'Automated pattern detection from current backend data.' : 'Automated pattern detection from 22 simulated captures.'}
        </p>
        {loading && live === null ? (
          <p className="text-sm text-slate-400">
            <Loader2 className="inline h-4 w-4 animate-spin mr-2" /> Loading insights…
          </p>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {insights.map((i) => (
              <div key={i.headline} className="rounded-xl bg-[#030303]/60 border border-white/10 p-4">
                <div className="font-bold text-white">{i.headline}</div>
                <div className="text-xs text-slate-400 mt-1">{i.detail}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
