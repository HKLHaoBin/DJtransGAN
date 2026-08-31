<template>
  <div class="mix-layout">
    <div class="mix-main">
      <div class="panel" style="margin-bottom: 1rem">
        <div class="row" style="justify-content: space-between">
          <h1 style="margin: 0">Mix 工作台</h1>
          <span :class="healthClass">{{ healthLabel }}</span>
        </div>
        <p class="muted" style="margin: 0.5rem 0 0">
          上传两首歌，设定 cue（秒），GAN 会在 cue 附近约 60 秒窗口内自动调 EQ 与 fader。切换页面后参数与文件会保留。
        </p>
      </div>

      <div class="grid-2" style="margin-bottom: 1rem">
        <section class="panel">
          <h2>Prev</h2>
          <div class="file-row">
            <input type="file" accept="audio/*" @change="onFile('prev', $event)" />
            <span class="file-name" v-if="draft.prevFile">{{ draft.prevFile.name }}</span>
            <button type="button" class="chip" v-if="draft.prevFile" @click="clearMixFile('prev')">清除</button>
          </div>
          <div class="row" style="margin-top: 0.75rem; align-items: flex-end">
            <label class="field">
              cue 方式
              <select v-model="draft.prevCueMode">
                <option value="from_end">从结尾倒数</option>
                <option value="absolute">从开头计时</option>
              </select>
            </label>
            <label class="field" v-if="draft.prevCueMode === 'from_end'">
              倒数（秒）
              <input v-model.number="draft.prevFromEnd" type="number" min="0" step="0.1" />
            </label>
            <label class="field" v-else>
              cue（秒）
              <input v-model.number="draft.prevCue" type="number" min="0" step="0.1" />
            </label>
          </div>
          <div class="row" v-if="draft.prevCueMode === 'from_end'" style="margin-top: 0.5rem">
            <button type="button" class="chip" @click="draft.prevFromEnd = 15">倒数 15s</button>
            <button type="button" class="chip" @click="draft.prevFromEnd = 30">倒数 30s</button>
            <button type="button" class="chip" @click="draft.prevFromEnd = 45">倒数 45s</button>
            <button type="button" class="chip" @click="draft.prevFromEnd = 60">倒数 60s</button>
            <span class="muted" v-if="draft.prevDuration">
              → cue {{ draft.prevCue.toFixed(1) }}s / 总长 {{ draft.prevDuration.toFixed(1) }}s
            </span>
          </div>
          <WaveCue
            v-model="draft.prevCue"
            role="prev"
            :file="draft.prevFile"
            style="margin-top: 0.75rem"
            @duration="onPrevDuration"
          />
        </section>
        <section class="panel">
          <h2>Next</h2>
          <div class="file-row">
            <input type="file" accept="audio/*" @change="onFile('next', $event)" />
            <span class="file-name" v-if="draft.nextFile">{{ draft.nextFile.name }}</span>
            <button type="button" class="chip" v-if="draft.nextFile" @click="clearMixFile('next')">清除</button>
          </div>
          <label class="field" style="margin-top: 0.75rem">
            cue（秒，从开头）
            <input v-model.number="draft.nextCue" type="number" min="0" step="0.1" />
          </label>
          <WaveCue v-model="draft.nextCue" role="next" :file="draft.nextFile" style="margin-top: 0.75rem" />
        </section>
      </div>

      <section class="panel" style="margin-bottom: 1rem">
        <h2 style="margin-top: 0">本次混音选项</h2>
        <div class="row" style="flex-wrap: wrap; gap: 1rem 1.5rem">
          <label class="check-inline">
            <input v-model="draft.matchBpm" type="checkbox" />
            匹配 BPM（整轨变速）
          </label>
          <label class="check-inline">
            <input v-model="draft.alignCue" type="checkbox" />
            对齐 cue 窗口
          </label>
          <RouterLink class="muted" to="/settings">改默认值 →</RouterLink>
        </div>
        <p class="muted" style="margin: 0.5rem 0 0; font-size: 0.85rem">
          曲速差大时请关掉「匹配 BPM」，否则 Next 会被拉到 Prev 的速度。
        </p>
      </section>

      <section class="panel" style="margin-bottom: 1rem">
        <div class="row">
          <button class="primary" :disabled="!canRun || busy" @click="run">
            {{ busy ? '混音中…' : '开始混音' }}
          </button>
          <button type="button" :disabled="busy" @click="restoreLast">恢复上次结果</button>
          <span class="muted" v-if="job">{{ job.message }} ({{ job.step }}/{{ job.total }})</span>
          <RouterLink v-if="job?.status === 'done'" class="muted" :to="{ name: 'results', query: { id: job.id } }">
            在结果页打开
          </RouterLink>
          <span class="status-err" v-if="error">{{ error }}</span>
        </div>
        <div class="progress" style="margin-top: 0.75rem">
          <i :style="{ width: progressPct + '%' }" />
        </div>
        <div class="row muted" style="margin-top: 0.5rem" v-if="job?.meta">
          <span class="pill" v-if="job.meta.prev_bpm != null">Prev BPM {{ Number(job.meta.prev_bpm).toFixed(1) }}</span>
          <span class="pill" v-if="job.meta.next_bpm != null">Next BPM {{ Number(job.meta.next_bpm).toFixed(1) }}</span>
          <span class="pill" v-if="job.meta.match_bpm != null">BPM匹配 {{ job.meta.match_bpm ? '开' : '关' }}</span>
          <span class="pill" v-if="job.meta.prev_cue != null">校正 Prev cue {{ Number(job.meta.prev_cue).toFixed(2) }}s</span>
          <span class="pill" v-if="job.meta.next_cue != null">校正 Next cue {{ Number(job.meta.next_cue).toFixed(2) }}s</span>
        </div>
      </section>

      <div class="grid-2" style="margin-bottom: 1rem" v-if="job?.status === 'done'">
        <section class="panel">
          <h3>过渡段 short</h3>
          <audio controls :src="shortUrl" style="width: 100%" />
        </section>
        <section class="panel">
          <h3>完整拼接 full</h3>
          <audio controls :src="fullUrl" style="width: 100%" />
        </section>
      </div>
      <p class="muted" v-if="job?.status === 'done'" style="margin: -0.5rem 0 1rem">
        任务 {{ job.id }} · 也可在磁盘打开
        <code>results/web-jobs/{{ job.id }}/</code>
      </p>

      <section class="panel" v-if="params">
        <h2>混音器曲线</h2>
        <p class="muted">Prev/Next 的 fader 与四段 EQ band（由 generator 的 mix_out 降采样）。</p>
        <CurvesChart :params="params" />
      </section>
    </div>

    <aside class="panel mix-aside">
      <h2 style="margin-top: 0">当前选用</h2>
      <div class="aside-slot">
        <div class="aside-label">Prev</div>
        <div class="aside-file" :class="{ empty: !draft.prevFile }">
          {{ draft.prevFile?.name || draft.prevFileName || '未选择' }}
        </div>
        <button
          type="button"
          class="chip"
          :disabled="!draft.prevFile"
          @click="clearMixFile('prev')"
        >
          清除
        </button>
      </div>
      <div class="aside-slot">
        <div class="aside-label">Next</div>
        <div class="aside-file" :class="{ empty: !draft.nextFile }">
          {{ draft.nextFile?.name || draft.nextFileName || '未选择' }}
        </div>
        <button
          type="button"
          class="chip"
          :disabled="!draft.nextFile"
          @click="clearMixFile('next')"
        >
          清除
        </button>
      </div>

      <h2>最近文件</h2>
      <p class="muted" style="margin: 0 0 0.75rem; font-size: 0.8rem">
        点一下即可回选，不必再打开系统文件框。刷新后仍可用（本机 IndexedDB）。
      </p>
      <ul class="recent-list" v-if="draft.recent.length">
        <li v-for="item in draft.recent" :key="item.id" class="recent-item">
          <div class="recent-meta">
            <div class="recent-name" :title="item.name">{{ item.name }}</div>
            <div class="muted" style="font-size: 0.75rem">
              {{ formatBytes(item.size) }}
              <span v-if="item.id === draft.prevFileId"> · Prev</span>
              <span v-if="item.id === draft.nextFileId"> · Next</span>
            </div>
          </div>
          <div class="recent-actions">
            <button type="button" class="chip" @click="pickRecent('prev', item.id)">Prev</button>
            <button type="button" class="chip" @click="pickRecent('next', item.id)">Next</button>
          </div>
        </li>
      </ul>
      <p class="muted" v-else style="font-size: 0.85rem">还没有历史文件，选歌后会出现在这里。</p>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, onActivated, onDeactivated, ref, watch } from 'vue'
import WaveCue from '@/components/WaveCue.vue'
import CurvesChart from '@/components/CurvesChart.vue'
import {
  createJob,
  fetchHealth,
  fetchJob,
  fetchLatestJob,
  fetchParams,
  jobAudioUrl,
  type Health,
  type Job,
  type MixParams,
} from '@/api'
import {
  applyRecentAs,
  clearMixFile,
  formatBytes,
  initMixDraft,
  mixDraft,
  setMixFile,
} from '@/mixDraft'

defineOptions({ name: 'MixView' })

const LAST_JOB_KEY = 'djtransgan.lastJobId'

const draft = mixDraft
const job = ref<Job | null>(null)
const params = ref<MixParams | null>(null)
const error = ref('')
const health = ref<Health | null>(null)
const busy = ref(false)
let pollTimer: number | undefined

const canRun = computed(() => !!draft.prevFile && !!draft.nextFile)
const progressPct = computed(() => {
  if (!job.value?.total) return 0
  return Math.min(100, Math.round((job.value.step / job.value.total) * 100))
})
const shortUrl = computed(() => (job.value?.status === 'done' ? jobAudioUrl(job.value.id, 'short') : ''))
const fullUrl = computed(() => (job.value?.status === 'done' ? jobAudioUrl(job.value.id, 'full') : ''))
const healthLabel = computed(() => {
  if (!health.value) return '检查服务…'
  if (health.value.ok) return '后端就绪'
  const bits = []
  if (!health.value.model.loaded) bits.push('模型未加载')
  if (!health.value.rubberband.available) bits.push('缺少 rubberband')
  return bits.join(' · ') || '未就绪'
})
const healthClass = computed(() => (health.value?.ok ? 'status-ok' : 'status-warn'))

function rememberJob(id: string) {
  try {
    localStorage.setItem(LAST_JOB_KEY, id)
  } catch {
    /* ignore quota */
  }
}

async function attachJob(j: Job) {
  job.value = j
  rememberJob(j.id)
  if (j.status === 'done') {
    busy.value = false
    params.value = await fetchParams(j.id)
  } else if (j.status === 'running' || j.status === 'queued') {
    busy.value = true
    await poll(j.id)
  } else if (j.status === 'error') {
    busy.value = false
    error.value = j.error || j.message
  }
}

function applyPrevFromEnd() {
  if (draft.prevCueMode !== 'from_end') return
  if (!draft.prevDuration) return
  const t = Math.max(0, draft.prevDuration - Math.max(0, draft.prevFromEnd))
  draft.prevCue = Number(t.toFixed(2))
}

function onPrevDuration(seconds: number) {
  draft.prevDuration = seconds
  applyPrevFromEnd()
}

async function onFile(which: 'prev' | 'next', ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  if (file) await setMixFile(which, file)
  input.value = ''
}

async function pickRecent(which: 'prev' | 'next', id: string) {
  error.value = ''
  const ok = await applyRecentAs(which, id)
  if (!ok) error.value = '无法回选该文件（可能已被清除），请重新上传'
}

watch(
  () => draft.prevFromEnd,
  () => applyPrevFromEnd(),
)
watch(
  () => draft.prevCueMode,
  () => {
    if (draft.prevCueMode === 'from_end') applyPrevFromEnd()
  },
)
watch(
  () => draft.prevCue,
  (v) => {
    if (draft.prevCueMode !== 'from_end' || !draft.prevDuration) return
    const offset = Math.max(0, draft.prevDuration - v)
    if (Math.abs(offset - draft.prevFromEnd) > 0.2) {
      draft.prevFromEnd = Number(offset.toFixed(2))
    }
  },
)

async function refreshHealth() {
  try {
    health.value = await fetchHealth()
  } catch {
    health.value = null
  }
}

function stopPoll() {
  if (pollTimer) window.clearInterval(pollTimer)
  pollTimer = undefined
}

async function poll(id: string) {
  stopPoll()
  pollTimer = window.setInterval(async () => {
    try {
      const j = await fetchJob(id)
      job.value = j
      rememberJob(id)
      if (j.status === 'done') {
        stopPoll()
        busy.value = false
        params.value = await fetchParams(id)
      } else if (j.status === 'error') {
        stopPoll()
        busy.value = false
        error.value = j.error || j.message
      }
    } catch (e) {
      stopPoll()
      busy.value = false
      error.value = e instanceof Error ? e.message : String(e)
    }
  }, 1000)
}

async function run() {
  if (!draft.prevFile || !draft.nextFile) return
  error.value = ''
  params.value = null
  busy.value = true
  try {
    const created = await createJob(draft.prevFile, draft.nextFile, draft.prevCue, draft.nextCue, {
      matchBpm: draft.matchBpm,
      alignCue: draft.alignCue,
    })
    job.value = created
    rememberJob(created.id)
    await poll(created.id)
  } catch (e) {
    busy.value = false
    error.value = e instanceof Error ? e.message : String(e)
  }
}

async function restoreLast() {
  error.value = ''
  try {
    const saved = localStorage.getItem(LAST_JOB_KEY)
    if (saved) {
      await attachJob(await fetchJob(saved))
      return
    }
    await attachJob(await fetchLatestJob())
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  }
}

onMounted(async () => {
  await initMixDraft()
  await refreshHealth()
  try {
    const saved = localStorage.getItem(LAST_JOB_KEY)
    if (saved) {
      await attachJob(await fetchJob(saved))
      return
    }
    await attachJob(await fetchLatestJob())
  } catch {
    /* no prior job */
  }
})

onActivated(() => {
  if (job.value && (job.value.status === 'running' || job.value.status === 'queued') && !pollTimer) {
    void poll(job.value.id)
  }
})

onDeactivated(stopPoll)
onBeforeUnmount(stopPoll)
</script>

