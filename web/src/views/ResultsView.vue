<template>
  <div>
    <section class="panel" style="margin-bottom: 1rem">
      <div class="row" style="justify-content: space-between; align-items: baseline">
        <div>
          <h1 style="margin: 0">混音结果</h1>
          <p class="muted" style="margin: 0.5rem 0 0">
            历次完成的 Mix 任务，存在 <code>results/web-jobs/</code>。跑多次后都在这里回听。
          </p>
        </div>
        <button type="button" :disabled="loading" @click="reload">
          {{ loading ? '刷新中…' : '刷新列表' }}
        </button>
      </div>
      <p class="status-err" v-if="error" style="margin: 0.75rem 0 0">{{ error }}</p>
    </section>

    <p class="muted" v-if="!loading && !jobs.length">还没有完成的任务。去 Mix 页跑一次即可。</p>

    <div class="results-layout" v-if="jobs.length">
      <aside class="panel results-list">
        <button
          v-for="j in jobs"
          :key="j.id"
          type="button"
          class="result-item"
          :class="{ active: selectedId === j.id }"
          @click="select(j.id)"
        >
          <div class="result-item-top">
            <strong>{{ j.id }}</strong>
            <span class="muted">{{ formatWhen(j.mtime) }}</span>
          </div>
          <div class="muted result-item-sub">
            {{ trackLabel(j) }}
          </div>
          <div class="muted result-item-sub">
            short {{ formatMb(j.short_bytes) }} · full {{ formatMb(j.full_bytes) }}
          </div>
        </button>
      </aside>

      <section class="panel" v-if="selectedId">
        <h2 style="margin-top: 0">{{ selectedId }}</h2>
        <div class="row muted" style="margin-bottom: 0.75rem" v-if="selectedMeta">
          <span class="pill" v-if="selectedMeta.prev_bpm != null">
            Prev BPM {{ Number(selectedMeta.prev_bpm).toFixed(1) }}
          </span>
          <span class="pill" v-if="selectedMeta.next_bpm != null">
            Next BPM {{ Number(selectedMeta.next_bpm).toFixed(1) }}
          </span>
          <span class="pill" v-if="selectedMeta.prev_cue != null">
            Prev cue {{ Number(selectedMeta.prev_cue).toFixed(2) }}s
          </span>
          <span class="pill" v-if="selectedMeta.next_cue != null">
            Next cue {{ Number(selectedMeta.next_cue).toFixed(2) }}s
          </span>
        </div>
        <p class="muted" style="margin-top: 0">
          磁盘路径 <code>results/web-jobs/{{ selectedId }}/</code>
        </p>

        <div class="grid-2" style="margin: 1rem 0">
          <div>
            <h3>过渡段 short</h3>
            <audio controls :src="jobAudioUrl(selectedId, 'short')" style="width: 100%" />
          </div>
          <div>
            <h3>完整拼接 full</h3>
            <audio controls :src="jobAudioUrl(selectedId, 'full')" style="width: 100%" />
          </div>
        </div>

        <div v-if="params">
          <h3>混音器曲线</h3>
          <CurvesChart :params="params" />
        </div>
        <p class="muted" v-else-if="loadingParams">加载曲线…</p>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import CurvesChart from '@/components/CurvesChart.vue'
import {
  fetchJobList,
  fetchParams,
  jobAudioUrl,
  type JobListItem,
  type MixParams,
} from '@/api'

const route = useRoute()
const jobs = ref<JobListItem[]>([])
const selectedId = ref('')
const params = ref<MixParams | null>(null)
const loading = ref(false)
const loadingParams = ref(false)
const error = ref('')

const selected = computed(() => jobs.value.find((j) => j.id === selectedId.value) ?? null)
const selectedMeta = computed(() => selected.value?.meta ?? null)

function formatMb(n?: number) {
  if (n == null) return '—'
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

function formatWhen(mtime?: number) {
  if (!mtime) return ''
  return new Date(mtime * 1000).toLocaleString()
}

function trackLabel(j: JobListItem) {
  const s = j.sources || {}
  const prev = (s.prev as string) || '?'
  const next = (s.next as string) || '?'
  return `${prev} → ${next}`
}

async function select(id: string) {
  selectedId.value = id
  params.value = null
  loadingParams.value = true
  try {
    params.value = await fetchParams(id)
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loadingParams.value = false
  }
}

async function reload() {
  loading.value = true
  error.value = ''
  try {
    jobs.value = await fetchJobList()
    const want = (route.query.id as string) || selectedId.value || jobs.value[0]?.id
    if (want && jobs.value.some((j) => j.id === want)) {
      await select(want)
    } else if (jobs.value[0]) {
      await select(jobs.value[0].id)
    } else {
      selectedId.value = ''
      params.value = null
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

onMounted(reload)
watch(
  () => route.query.id,
  (id) => {
    if (typeof id === 'string' && id && id !== selectedId.value) {
      if (jobs.value.some((j) => j.id === id)) void select(id)
    }
  },
)
</script>

<style scoped>
.results-layout {
  display: grid;
  grid-template-columns: minmax(220px, 320px) 1fr;
  gap: 1rem;
  align-items: start;
}
.results-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: calc(100vh - 10rem);
  overflow: auto;
  padding: 0.75rem;
}
.result-item {
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 0.65rem 0.75rem;
  color: inherit;
  cursor: pointer;
}
.result-item:hover {
  border-color: #3b4a5e;
  background: rgba(255, 255, 255, 0.03);
}
.result-item.active {
  border-color: #5eead4;
  background: rgba(94, 234, 212, 0.08);
}
.result-item-top {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}
.result-item-sub {
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 800px) {
  .results-layout {
    grid-template-columns: 1fr;
  }
  .results-list {
    max-height: 240px;
  }
}
</style>
