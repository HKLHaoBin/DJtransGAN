<template>
  <div>
    <div ref="el" class="wave" />
    <div class="row" style="margin-top: 0.5rem; justify-content: space-between">
      <span class="muted" v-if="duration">时长 {{ duration.toFixed(1) }}s</span>
      <span class="muted">cue {{ modelValue.toFixed(1) }}s</span>
    </div>
    <p class="muted" style="margin: 0.35rem 0 0; font-size: 0.8rem">
      {{ hint }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import WaveSurfer from 'wavesurfer.js'

const props = withDefaults(
  defineProps<{
    file?: File | null
    modelValue: number
    /** prev: 左侧为保留段；next: 右侧为切入后保留段 */
    role?: 'prev' | 'next'
  }>(),
  { role: 'prev' },
)

const emit = defineEmits<{
  (e: 'update:modelValue', v: number): void
  (e: 'duration', seconds: number): void
}>()

const el = ref<HTMLElement | null>(null)
const duration = ref(0)
let ws: WaveSurfer | null = null
let objectUrl: string | null = null

const dim = '#3b4a5e'
const lit = '#5eead4'

const hint = computed(() =>
  props.role === 'next'
    ? '亮色=切入后保留（右侧）；灰=cue 之前。点击波形设 cue。'
    : '亮色=切出前保留（左侧）；灰=cue 之后。点击波形设 cue。',
)

function destroy() {
  ws?.destroy()
  ws = null
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = null
  }
}

function emitCue(seconds: number) {
  const dur = duration.value || ws?.getDuration() || 0
  const t = Math.min(Math.max(seconds, 0), dur || seconds)
  emit('update:modelValue', Number(t.toFixed(2)))
}

async function load() {
  destroy()
  if (!el.value || !props.file) return

  // WaveSurfer progress fills 0→cursor. For next we invert colors so the
  // kept (post-cue) side on the right stays lit and the pre-cue side is dim.
  const isNext = props.role === 'next'
  objectUrl = URL.createObjectURL(props.file)
  ws = WaveSurfer.create({
    container: el.value,
    height: 88,
    waveColor: isNext ? lit : dim,
    progressColor: isNext ? dim : lit,
    cursorColor: '#fbbf24',
    cursorWidth: 2,
    url: objectUrl,
  })
  ws.on('ready', () => {
    duration.value = ws?.getDuration() ?? 0
    emit('duration', duration.value)
    if (duration.value > 0) {
      const t = Math.min(Math.max(props.modelValue, 0), duration.value)
      ws?.setTime(t)
    }
  })
  // interaction gives seconds; click gives relativeX in [0,1] — do not use click as time
  ws.on('interaction', (newTime: number) => {
    emitCue(newTime)
  })
}

onMounted(load)
watch(() => props.file, load)
watch(
  () => props.modelValue,
  (v) => {
    if (!ws || !duration.value) return
    const cur = ws.getCurrentTime()
    if (Math.abs(cur - v) > 0.15) ws.setTime(v)
  },
)

onBeforeUnmount(destroy)
</script>
