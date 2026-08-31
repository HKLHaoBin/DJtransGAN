export type JobStatus = 'queued' | 'running' | 'done' | 'error'

export interface Job {
  id: string
  status: JobStatus
  step: number
  total: number
  message: string
  error?: string | null
  meta?: Record<string, unknown>
  post_cue?: number[]
  has_short?: boolean
  has_full?: boolean
  has_params?: boolean
}

export interface Health {
  ok: boolean
  model: { loaded: boolean; weights?: string | null; error?: string | null }
  rubberband: { available: boolean; path?: string | null }
  limits: { max_upload_mb: number; allowed_suffixes: string[] }
}

export interface DemoGroups {
  groups: { id: string; index: number; category: string; label: string }[]
  tracks: string[]
  track_labels: Record<string, string>
}

export interface MixParams {
  n_time: number
  sample_rate: number
  band_freqs: number[]
  band_labels: string[]
  tracks: Record<
    string,
    {
      fader?: number[]
      fader_time?: number[]
      band?: number[][]
    }
  >
  post_cue?: number[]
  meta?: Record<string, unknown>
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || res.statusText)
  }
  return res.json() as Promise<T>
}

export async function fetchHealth(): Promise<Health> {
  return parseJson(await fetch('/api/health'))
}

export async function fetchDemoGroups(): Promise<DemoGroups> {
  return parseJson(await fetch('/api/demo/groups'))
}

export function demoAudioUrl(index: number, name: string): string {
  return `/api/demo/audio/${index}/${name}`
}

export async function createJob(
  prev: File,
  next: File,
  prevCue: number,
  nextCue: number,
  opts?: { matchBpm?: boolean; alignCue?: boolean },
): Promise<Job> {
  const body = new FormData()
  body.append('prev', prev)
  body.append('next', next)
  body.append('prev_cue', String(prevCue))
  body.append('next_cue', String(nextCue))
  body.append('match_bpm', opts?.matchBpm ? 'true' : 'false')
  body.append('align_cue', opts?.alignCue === false ? 'false' : 'true')
  return parseJson(await fetch('/api/jobs', { method: 'POST', body }))
}

export async function fetchJob(id: string): Promise<Job> {
  return parseJson(await fetch(`/api/jobs/${id}`))
}

export interface JobListItem {
  id: string
  status: JobStatus
  mtime?: number
  short_bytes?: number
  full_bytes?: number
  has_short?: boolean
  has_full?: boolean
  has_params?: boolean
  sources?: Record<string, unknown>
  meta?: Record<string, unknown>
  post_cue?: number[]
}

export async function fetchJobList(): Promise<JobListItem[]> {
  const data = await parseJson<{ jobs: JobListItem[] }>(await fetch('/api/jobs'))
  return data.jobs
}

export async function fetchLatestJob(): Promise<Job> {
  return parseJson(await fetch('/api/jobs/latest'))
}

export async function fetchParams(id: string): Promise<MixParams> {
  return parseJson(await fetch(`/api/jobs/${id}/params`))
}

export function jobAudioUrl(id: string, kind: 'short' | 'full'): string {
  return `/api/jobs/${id}/audio/${kind}`
}
