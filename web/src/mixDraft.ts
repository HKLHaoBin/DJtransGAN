import { reactive, watch } from 'vue'
import { loadSettings, type PrevCueMode } from '@/settings'
import {
  fileIdentity,
  getRecentBlob,
  listRecentMeta,
  rememberRecentFile,
  type RecentFileMeta,
} from '@/recentAudio'

const DRAFT_KEY = 'djtransgan.mixDraft.v1'

export interface MixDraftParams {
  prevCueMode: PrevCueMode
  prevFromEnd: number
  prevDuration: number
  prevCue: number
  nextCue: number
  matchBpm: boolean
  alignCue: boolean
  prevFileId: string | null
  nextFileId: string | null
  prevFileName: string | null
  nextFileName: string | null
}

export interface MixDraftState extends MixDraftParams {
  prevFile: File | null
  nextFile: File | null
  recent: RecentFileMeta[]
  ready: boolean
}

function defaultsFromSettings(): MixDraftParams {
  const s = loadSettings()
  return {
    prevCueMode: s.prevCueMode,
    prevFromEnd: s.defaultPrevFromEnd,
    prevDuration: 0,
    prevCue: s.prevCueMode === 'absolute' ? s.defaultPrevCue : s.defaultPrevFromEnd,
    nextCue: s.defaultNextCue,
    matchBpm: s.matchBpm,
    alignCue: s.alignCue,
    prevFileId: null,
    nextFileId: null,
    prevFileName: null,
    nextFileName: null,
  }
}

function loadParams(): MixDraftParams {
  const base = defaultsFromSettings()
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return base
    const parsed = JSON.parse(raw) as Partial<MixDraftParams>
    return { ...base, ...parsed }
  } catch {
    return base
  }
}

function serialize(state: MixDraftState): MixDraftParams {
  return {
    prevCueMode: state.prevCueMode,
    prevFromEnd: state.prevFromEnd,
    prevDuration: state.prevDuration,
    prevCue: state.prevCue,
    nextCue: state.nextCue,
    matchBpm: state.matchBpm,
    alignCue: state.alignCue,
    prevFileId: state.prevFileId,
    nextFileId: state.nextFileId,
    prevFileName: state.prevFileName,
    nextFileName: state.nextFileName,
  }
}

const initial = loadParams()

export const mixDraft = reactive<MixDraftState>({
  ...initial,
  prevFile: null,
  nextFile: null,
  recent: [],
  ready: false,
})

let persistTimer: number | undefined

export function persistMixDraft() {
  try {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(serialize(mixDraft)))
  } catch {
    /* quota */
  }
}

function schedulePersist() {
  if (persistTimer) window.clearTimeout(persistTimer)
  persistTimer = window.setTimeout(() => persistMixDraft(), 120)
}

watch(
  () => [
    mixDraft.prevCueMode,
    mixDraft.prevFromEnd,
    mixDraft.prevDuration,
    mixDraft.prevCue,
    mixDraft.nextCue,
    mixDraft.matchBpm,
    mixDraft.alignCue,
    mixDraft.prevFileId,
    mixDraft.nextFileId,
    mixDraft.prevFileName,
    mixDraft.nextFileName,
  ],
  schedulePersist,
  { deep: false },
)

async function refreshRecent() {
  mixDraft.recent = await listRecentMeta()
}

async function restoreFileFromId(id: string | null): Promise<File | null> {
  if (!id) return null
  const blob = await getRecentBlob(id)
  if (!blob) return null
  const meta = mixDraft.recent.find((r) => r.id === id)
  const name = meta?.name || (id.includes('::') ? id.split('::')[0] : 'audio')
  const type = meta?.type || blob.type || 'audio/*'
  const lastModified = meta?.lastModified || Date.now()
  return new File([blob], name, { type, lastModified })
}

export async function initMixDraft() {
  if (mixDraft.ready) return
  await refreshRecent()
  if (!mixDraft.prevFile && mixDraft.prevFileId) {
    mixDraft.prevFile = await restoreFileFromId(mixDraft.prevFileId)
  }
  if (!mixDraft.nextFile && mixDraft.nextFileId) {
    mixDraft.nextFile = await restoreFileFromId(mixDraft.nextFileId)
  }
  mixDraft.ready = true
}

export async function setMixFile(which: 'prev' | 'next', file: File | null) {
  if (which === 'prev') {
    mixDraft.prevFile = file
    mixDraft.prevDuration = 0
    if (file) {
      const id = await rememberRecentFile(file)
      mixDraft.prevFileId = id
      mixDraft.prevFileName = file.name
      await refreshRecent()
    } else {
      mixDraft.prevFileId = null
      mixDraft.prevFileName = null
    }
  } else {
    mixDraft.nextFile = file
    if (file) {
      const id = await rememberRecentFile(file)
      mixDraft.nextFileId = id
      mixDraft.nextFileName = file.name
      await refreshRecent()
    } else {
      mixDraft.nextFileId = null
      mixDraft.nextFileName = null
    }
  }
  persistMixDraft()
}

export async function applyRecentAs(which: 'prev' | 'next', id: string) {
  const file = await restoreFileFromId(id)
  if (!file) {
    await refreshRecent()
    return false
  }
  await setMixFile(which, file)
  return true
}

export function clearMixFile(which: 'prev' | 'next') {
  void setMixFile(which, null)
}

export function formatBytes(n: number) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export { fileIdentity }
