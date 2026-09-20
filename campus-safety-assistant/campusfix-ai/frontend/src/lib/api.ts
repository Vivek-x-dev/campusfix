/** Typed client for the CampusFix FastAPI backend. */

const envUrl = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '');
export const API_BASE = envUrl !== undefined && envUrl !== '' ? envUrl : (import.meta.env.PROD ? '' : 'http://127.0.0.1:8000');

export interface DuplicateMatch {
  incident_id: string
  similarity: number
  location?: string
  issue?: string
}

export interface AnalysisResult {
  category?: string
  confidence?: number
  severity?: string
  risk?: string
  risk_score?: number
  action?: string
  department?: string
  summary?: string
  explanation?: string[]
  damage?: string
  caption?: string
  ocr_text?: string | null
  needs_human_review?: boolean
  model_version?: string
  inference_time_ms?: number
  decision?: string
  duplicate?: {
    is_duplicate?: boolean
    matches?: DuplicateMatch[]
  }
  // allow extra fields the backend may add
  [key: string]: unknown
}

export async function analyzeIncident(
  file: File | null,
  description: string,
  location: string,
  signal?: AbortSignal,
): Promise<AnalysisResult> {
  const form = new FormData()
  form.append('description', description)
  form.append('location', location)
  if (file) form.append('image', file, file.name)

  const res = await fetch(`${API_BASE}/ai/analyze`, {
    method: 'POST',
    body: form,
    signal,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`AI backend error ${res.status}: ${text || res.statusText}`)
  }
  return (await res.json()) as AnalysisResult
}

export async function checkBackendHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal })
    if (!res.ok) return false
    const data = (await res.json()) as { ok?: boolean }
    return data.ok === true
  } catch {
    return false
  }
}

/** A stored incident record (backend source of truth for dashboard/admin/analytics). */
export interface IncidentRecord {
  incident_id: string
  description: string
  location: string
  issue?: string
  category?: string
  severity?: string
  status?: string
  created_at?: string
  analysis?: AnalysisResult | null
  duplicate_of?: string | null
}

export const INCIDENT_STATUSES = ['Open', 'Assigned', 'In Progress', 'Resolved', 'Closed'] as const

async function expectOk(res: Response, what: string): Promise<unknown> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`${what} failed (${res.status}): ${text || res.statusText}`)
  }
  return res.json()
}

/** Analyze + save in one call (used by the Report page). */
export async function createIncident(
  file: File | null,
  description: string,
  location: string,
  signal?: AbortSignal,
): Promise<{ incident: IncidentRecord; analysis: AnalysisResult }> {
  const form = new FormData()
  form.append('description', description)
  form.append('location', location)
  if (file) form.append('image', file, file.name)
  const res = await fetch(`${API_BASE}/incidents`, { method: 'POST', body: form, signal })
  return (await expectOk(res, 'Report submit')) as { incident: IncidentRecord; analysis: AnalysisResult }
}

/** Save an already-computed analysis (used by the AI Analysis page). */
export async function saveAnalysisResult(
  description: string,
  location: string,
  analysis: AnalysisResult,
  signal?: AbortSignal,
): Promise<{ incident: IncidentRecord }> {
  const res = await fetch(`${API_BASE}/incidents/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description, location, analysis }),
    signal,
  })
  return (await expectOk(res, 'Save incident')) as { incident: IncidentRecord }
}

export async function listIncidents(signal?: AbortSignal): Promise<IncidentRecord[]> {
  const res = await fetch(`${API_BASE}/incidents`, { signal })
  const data = (await expectOk(res, 'Load incidents')) as { incidents?: IncidentRecord[] }
  return data.incidents ?? []
}

export async function getIncident(id: string, signal?: AbortSignal): Promise<IncidentRecord> {
  const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(id)}`, { signal })
  const data = (await expectOk(res, 'Load incident')) as { incident: IncidentRecord }
  return data.incident
}

export async function updateIncidentStatus(
  id: string,
  status: string,
  note?: string,
): Promise<IncidentRecord> {
  const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(id)}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, note }),
  })
  const data = (await expectOk(res, 'Status update')) as { incident: IncidentRecord }
  return data.incident
}

export interface Insight {
  headline: string
  detail: string
}

export async function getInsights(signal?: AbortSignal): Promise<Insight[]> {
  const res = await fetch(`${API_BASE}/ai/insights`, { signal })
  const data = (await expectOk(res, 'Load insights')) as { insights?: Insight[] }
  return data.insights ?? []
}
