import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { UploadCloud, MapPin, Check, Loader2, AlertTriangle, Wifi, WifiOff } from 'lucide-react'
import { Link } from 'react-router-dom'
import { checkBackendHealth, createIncident, type AnalysisResult, type IncidentRecord } from '../lib/api'

type Status = 'idle' | 'submitting' | 'success' | 'error'

export default function ReportIncident() {
  const [drag, setDrag] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [description, setDescription] = useState('')
  const [location, setLocation] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [savedIncident, setSavedIncident] = useState<IncidentRecord | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [backendUp, setBackendUp] = useState<boolean | null>(null)

  useEffect(() => {
    checkBackendHealth().then(setBackendUp).catch(() => setBackendUp(false))
  }, [])

  const pickFile = (f: File | undefined) => {
    if (!f) return
    if (f.size > 10 * 1024 * 1024) {
      setError('Image must be under 10MB.')
      setStatus('error')
      return
    }
    setError(null)
    if (status === 'error' && !result) setStatus('idle')
    setFile(f)
    setPreview((prev) => {
      if (prev) URL.revokeObjectURL(prev)
      return URL.createObjectURL(f)
    })
  }

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please attach a photo of the issue first.')
      setStatus('error')
      return
    }
    setStatus('submitting')
    setError(null)
    setResult(null)
    setSavedIncident(null)
    try {
      // Single call: vision analysis + save to dashboard store
      const { incident, analysis } = await createIncident(file, description, location)
      setSavedIncident(incident)
      setResult(analysis)
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed. Is the backend running on port 8000?')
      setStatus('error')
    }
  }

  const dup = result?.duplicate
  const topMatch = dup?.matches?.[0]

  return (
    <div className="mx-auto max-w-3xl px-6 lg:px-8 py-12 space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-4xl font-extrabold tracking-tight text-white mb-2">Report Incident</h1>
          <p className="text-slate-400">Upload a photo, describe the issue, and select the location. Our AI handles the rest.</p>
        </div>
        <div
          className={`mt-1 flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium ${
            backendUp === null
              ? 'border-white/10 text-slate-400'
              : backendUp
                ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300'
                : 'border-rose-400/30 bg-rose-400/10 text-rose-300'
          }`}
          title="FastAPI backend status"
        >
          {backendUp === null ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : backendUp ? (
            <Wifi className="h-3.5 w-3.5" />
          ) : (
            <WifiOff className="h-3.5 w-3.5" />
          )}
          {backendUp === null ? 'Checking AI…' : backendUp ? 'AI connected' : 'AI offline'}
        </div>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDrag(true)
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          pickFile(e.dataTransfer.files[0])
        }}
        className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 transition-all ${drag ? 'border-amber-400 bg-amber-400/5' : 'border-white/10 bg-white/[0.02]'}`}
      >
        <UploadCloud className="h-12 w-12 text-amber-300 mb-4" />
        <p className="text-lg font-medium text-white mb-1">Drag and drop your image</p>
        <p className="text-sm text-slate-400 mb-4">PNG, JPG, or WEBP up to 10MB</p>
        <label className="cursor-pointer rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-bold text-[#030303] hover:bg-amber-300">
          Select File
          <input
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
        </label>
        {file && <p className="mt-3 text-xs text-slate-400">{file.name}</p>}
      </div>

      <AnimatePresence>
        {preview && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <div className="rounded-xl overflow-hidden border border-white/10 shadow-2xl shadow-black/40">
              <img src={preview} alt="Preview" className="w-full object-cover max-h-[400px]" />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={onSubmit} className="space-y-6">
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label htmlFor="desc" className="mb-2 block text-sm font-medium text-slate-200">
              Description
            </label>
            <textarea
              id="desc"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg bg-[#0a0a0a] border border-white/10 p-3 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-400/40 resize-none"
              placeholder="What happened? Is there immediate risk?"
            />
          </div>
          <div>
            <label htmlFor="loc" className="mb-2 block text-sm font-medium text-slate-200">
              Location
            </label>
            <div className="relative">
              <MapPin className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                id="loc"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full rounded-lg bg-[#0a0a0a] border border-white/10 pl-10 pr-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-amber-400/40"
                placeholder="Building, floor, or zone"
              />
            </div>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button
            type="submit"
            disabled={status === 'submitting'}
            className="rounded-lg bg-amber-400 px-8 py-3 text-base font-bold text-[#030303] hover:bg-amber-300 disabled:opacity-50 shadow-lg shadow-amber-400/20 transition-colors flex items-center gap-2"
          >
            {status === 'submitting' && <Loader2 className="h-5 w-5 animate-spin" />}
            {status === 'submitting' ? 'Analyzing with AI…' : status === 'success' ? 'Analyzed' : 'Submit to AI Pipeline'}
          </button>
          {status === 'success' && (
            <span className="flex items-center gap-2 text-sm text-emerald-400 font-medium">
              <Check className="h-4 w-4" /> Vision + risk model responded
            </span>
          )}
        </div>
        {backendUp === false && (
          <p className="text-xs text-slate-500">
            Backend looks offline — start it with{' '}
            <code className="text-slate-300">uvicorn backend.app.main:app --host 127.0.0.1 --port 8000</code>{' '}
            from the <code className="text-slate-300">campusfix-ai</code> folder.
          </p>
        )}
      </form>

      <AnimatePresence>
        {status === 'error' && error && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-start gap-3 rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200"
          >
            <AlertTriangle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </motion.div>
        )}

        {status === 'success' && result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-2xl border border-white/10 bg-[#0a0a0a] p-6 shadow-2xl shadow-black/40 space-y-4"
          >
            <h2 className="text-xl font-bold text-white">AI Triage Result</h2>
            {savedIncident && (
              <p className="text-xs font-mono text-emerald-300">
                Saved to dashboard as {savedIncident.incident_id} · status {savedIncident.status ?? 'Open'}
              </p>
            )}
            <div className="space-y-3">
              <ResultRow label="Category" value={result.category ?? '—'} />
              <ResultRow
                label="Confidence"
                value={typeof result.confidence === 'number' ? `${Math.round(result.confidence * 100)}%` : '—'}
              />
              <ResultRow label="Severity" value={result.severity ?? '—'} highlight />
              <ResultRow label="Risk" value={result.risk ?? (typeof result.risk_score === 'number' ? `${result.risk_score} / 10` : '—')} />
              <ResultRow label="Department" value={result.department ?? '—'} />
              <ResultRow label="Action" value={result.action ?? '—'} />
              {result.summary && <ResultRow label="Summary" value={result.summary} />}
              {dup?.is_duplicate && topMatch && (
                <ResultRow
                  label="Duplicate Warning"
                  value={`Possible match with ${topMatch.incident_id}${topMatch.location ? ` (${topMatch.location})` : ''}`}
                  warning
                />
              )}
              {typeof result.inference_time_ms === 'number' && (
                <p className="text-xs text-slate-500">
                  Analyzed in {(result.inference_time_ms / 1000).toFixed(1)}s
                  {result.model_version ? ` · ${result.model_version}` : ''}
                  {result.needs_human_review ? ' · flagged for human review' : ''}
                </p>
              )}
            </div>
            <div className="flex flex-wrap gap-3">
            {savedIncident && (
              <Link
                to={`/details/${savedIncident.incident_id}`}
                className="inline-block rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-bold text-[#030303] hover:bg-amber-300"
              >
                View saved incident
              </Link>
            )}
            <Link
              to="/dashboard"
              className="inline-block rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10"
            >
              Open dashboard
            </Link>
            <Link
              to="/analysis"
              className="inline-block rounded-lg border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-white hover:bg-white/10"
            >
              Open full AI pipeline
            </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function ResultRow({ label, value, highlight, warning }: { label: string; value: string; highlight?: boolean; warning?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg bg-white/[0.03] p-3 border border-white/5">
      <span className="text-sm text-slate-400 shrink-0">{label}</span>
      <span className={`text-sm font-bold text-right ${highlight ? 'text-rose-400' : warning ? 'text-amber-300' : 'text-white'}`}>
        {value}
      </span>
    </div>
  )
}
