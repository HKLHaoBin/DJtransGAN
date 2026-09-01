export type PrevCueMode = 'absolute' | 'from_end'

export interface StudioSettings {
  /** Smoothly match cue-local tempo only inside the Next transition window. */
  matchBpm: boolean
  /** Align cue windows through the same single transition time map. */
  alignCue: boolean
  /** How Prev cue is specified on Mix page. */
  prevCueMode: PrevCueMode
  /** Used when prevCueMode is absolute. */
  defaultPrevCue: number
  /** Seconds before end when prevCueMode is from_end. */
  defaultPrevFromEnd: number
  defaultNextCue: number
}

export const SETTINGS_KEY = 'djtransgan.studioSettings'

export const DEFAULT_SETTINGS: StudioSettings = {
  matchBpm: false,
  alignCue: true,
  prevCueMode: 'from_end',
  defaultPrevCue: 96,
  defaultPrevFromEnd: 30,
  defaultNextCue: 30,
}

export function loadSettings(): StudioSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (!raw) return { ...DEFAULT_SETTINGS }
    const parsed = JSON.parse(raw) as Partial<StudioSettings>
    return { ...DEFAULT_SETTINGS, ...parsed }
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export function saveSettings(s: StudioSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(s))
}
