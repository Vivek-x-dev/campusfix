import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import {
  UploadCloud,
  Brain,
  ListOrdered,
  ShieldCheck,
  Search,
  CheckCircle2,
  Loader2,
  AlertTriangle,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { analyzeIncident, saveAnalysisResult, API_BASE, type AnalysisResult } from '../lib/api'

const steps = [
  { id: 'upload', label: 'Upload Image', icon: UploadCloud, desc: 'Snap or select incident photo' },
  { id: 'vision', label: 'Vision Analysis', icon: Brain, desc: 'Classify category, caption, objects' },
  { id: 'classify', label: 'Classification', icon: ListOrdered, desc: 'Assign category with confidence' },
  { id: 'risk', label: 'Risk Assessment', icon: ShieldCheck, desc: 'Compute severity and risk score' },
  { id: 'duplicate', label: 'Duplicate Detection', icon: Search, desc: 'Check proximity + visual similarity' },
  { id: 'result', label: 'Result', icon: CheckCircle2, desc: 'Action + department recommendation' },
]

export default function AIAnalysis() {
  const [file, setFile] = useState<File | null>(null)
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [active, setActive] = useState(0)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [savedId, setSavedId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const timer = useRef<number | null>(null)

  useEffect(() => {
    return () => {
      if (timer.current !== null) window.clearInterval(timer.current)
    }
  }, [])

  const runAnalysis = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file || running) return
    setRunning(true)
    setError(null)
    setResult(null)
    setSavedId(null)
    setActive(0)
    // Animate the pipeline while the backend works (analysis can take ~15-20s on live vision)
    timer.current = window.setInterval(() => {
      setActive((a) => (a < steps.length - 2 ? a + 1 : a))
    }, 1500)
    try {
      const analysis = await analyzeIncident(file, description, location)
      setResult(analysis)
      setActive(steps.length - 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : `Analysis failed. Is the backend up at ${API_BASE}?`)
    } finally {
      if (timer.current !== null) window.clearInterval(timer.current)
      timer.current = null
      setRunning(false)
    }
  }

  const dup = result?.duplicate
  const topMatch = dup?.matches?.[0]

  const saveToDashboard = async () => {
    if (!result || saving) return
    setSaving(true)
    setError(null)
    try {
      const { incident } = await saveAnalysisResult(description, location, result)
      setSavedId(incident.incident_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 lg:px-8 py-12 space-y-12">
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">AI Analysis Pipeline</h1>
        <p className="text-slate-400">End-to-end multimodal triage from image to structured incident record.</p>
      </div>

      <form
        onSubmit={runAnalysis}
        className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-6 shadow-2xl shadow-black/40 flex flex-col md:flex-row gap-4 md:items-end"
      >
        <label className="cursor-pointer rounded-lg bg-white/5 border border-white/10 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10 whitespace-nowrap">
          {file ? file.name : 'Choose image…'}
          <input type="file" accept="image/*" hidden onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </label>
        <input
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (e.g. exposed wire near socket)"
          className="flex-1 rounded-lg bg-[#030303] border border-white/10 px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-400/40"
        />
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="Location (e.g. Lab 304)"
          className="md:w-56 rounded-lg bg-[#030303] border border-white/10 px-4 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-400/40"
        />
        <button
          type="submit"
          disabled={!file || running}
          className="rounded-lg bg-amber-400 px-6 py-2.5 text-sm font-bold text-[#030303] hover:bg-amber-300 disabled:opacity-50 flex items-center gap-2 whitespace-nowrap"
        >
          {running && <Loader2 className="h-4 w-4 animate-spin" />}
          {running ? 'Analyzing…' : 'Run live analysis'}
        </button>
      </form>

      <div className="flex flex-wrap gap-3 items-center justify-between">
        {steps.map((s, i) => (
          <div
            key={s.id}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all ${i <= active ? 'bg-amber-400/10 border-amber-400/30 text-amber-200' : 'bg-white/5 border-white/10 text-slate-500'}`}
          >
            <s.icon className={`h-5 w-5 ${i <= active ? 'text-amber-300' : 'text-slate-600'}`} />
            <div>
              <div className="text-xs font-bold uppercase tracking-wide">
                {i + 1}. {s.label}
              </div>
              <div className="text-xs text-slate-400">{s.desc}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-8 shadow-2xl shadow-black/40">
          <h2 className="text-xl font-bold text-white mb-6">Pipeline Flow</h2>
          <div className="space-y-4">
            {steps.map((s, i) => (
              <motion.div
                key={s.id}
                initial={{ opacity: 0.5 }}
                animate={{ opacity: i <= active ? 1 : 0.4, scale: i === active ? 1.02 : 1 }}
                className={`flex items-center gap-4 rounded-xl border p-4 transition-colors ${i === active ? 'border-amber-400/40 bg-amber-400/5' : 'border-white/5 bg-white/[0.02]'}`}
              >
                <div
                  className={`h-10 w-10 rounded-full flex items-center justify-center font-extrabold text-sm ${i <= active ? 'bg-amber-400 text-[#030303]' : 'bg-white/10 text-slate-500'}`}
                >
                  {i + 1}
                </div>
                <div>
                  <div className="font-semibold text-white">{s.label}</div>
                  <div className="text-xs text-slate-400">{s.desc}</div>
                  {i === active && running && <div className="mt-1 h-1.5 w-24 rounded-full bg-amber-400/60 animate-pulse" />}
                </div>
                {i <= active && (
                  <div className="ml-auto text-amber-300">
                    <CheckCircle2 className="h-5 w-5" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-8 shadow-2xl shadow-black/40">
          <h2 className="text-xl font-bold text-white mb-6">Analysis Result {result ? '— Live' : ''}</h2>
          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200">
              <AlertTriangle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}
          {!error && !result && (
            <p className="text-sm text-slate-400">
              {running
                ? 'Vision model is analyzing your photo — this can take ~15–20 seconds on a live call…'
                : 'Choose an image above and run a live analysis to see the real vision + risk output here.'}
            </p>
          )}
          {result && (
            <>
              <div className="space-y-4">
                <DataRow label="Category" value={result.category ?? '—'} />
                <DataRow
                  label="Confidence"
                  value={typeof result.confidence === 'number' ? `${Math.round(result.confidence * 100)}%` : '—'}
                />
                <DataRow label="Severity" value={result.severity ?? '—'} highlight />
                <DataRow label="Risk" value={result.risk ?? '—'} />
                <DataRow label="Department" value={result.department ?? '—'} />
                <DataRow label="Action" value={result.action ?? '—'} />
                {result.summary && <DataRow label="Summary" value={result.summary} />}
                {dup?.is_duplicate && topMatch && (
                  <DataRow
                    label="Duplicate Warning"
                    value={`Possible match with ${topMatch.incident_id}${topMatch.location ? ` (${topMatch.location})` : ''}`}
                    warning
                  />
                )}
              </div>
              <div className="mt-6 flex flex-wrap gap-3 items-center">
                {savedId ? (
                  <Link
                    to={`/details/${savedId}`}
                    className="rounded-lg bg-emerald-400 px-5 py-2.5 text-sm font-bold text-[#030303] hover:bg-emerald-300"
                  >
                    Saved as {savedId} — view it
                  </Link>
                ) : (
                  <button
                    onClick={saveToDashboard}
                    disabled={saving}
                    className="rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-bold text-[#030303] hover:bg-amber-300 disabled:opacity-50 flex items-center gap-2"
                  >
                    {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                    {saving ? 'Saving…' : 'Save to dashboard'}
                  </button>
                )}
                <Link
                  to="/report"
                  className="rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10"
                >
                  Report another
                </Link>
                <Link
                  to="/analytics"
                  className="rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10"
                >
                  View Trends
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function DataRow({ label, value, highlight, warning }: { label: string; value: string; highlight?: boolean; warning?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg bg-white/[0.03] p-3 border border-white/5">
      <span className="text-sm text-slate-400 shrink-0">{label}</span>
      <span className={`text-sm font-bold text-right ${highlight ? 'text-rose-400' : warning ? 'text-amber-300' : 'text-white'}`}>
        {value}
      </span>
    </div>
  )
}
