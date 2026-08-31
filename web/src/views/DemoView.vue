<template>
  <div>
    <section class="panel" style="margin-bottom: 1rem">
      <h1>论文试听对照</h1>
      <p class="muted" style="margin: 0">
        八组测试对：Prev / Next 与 Sum、Linear、Rule、GAN、Human。音频来自 demo-site，经 API 转发。
      </p>
    </section>

    <section v-for="cat in categories" :key="cat.key" class="panel" style="margin-bottom: 1rem">
      <h2>{{ cat.label }}</h2>
      <table class="table">
        <thead>
          <tr>
            <th></th>
            <th v-for="t in tracks" :key="t">{{ labels[t] || t }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="g in cat.groups" :key="g.id">
            <td>{{ g.id }}</td>
            <td v-for="t in tracks" :key="t">
              <audio controls preload="none" :src="demoAudioUrl(g.index, t)" />
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { demoAudioUrl, fetchDemoGroups, type DemoGroups } from '@/api'

const data = ref<DemoGroups | null>(null)
const tracks = computed(() => data.value?.tracks ?? [])
const labels = computed(() => data.value?.track_labels ?? {})

const categoryMeta: Record<string, string> = {
  'nv-nv': 'non-vocal → non-vocal (nv-nv)',
  'nv-v': 'non-vocal → vocal (nv-v)',
  'v-nv': 'vocal → non-vocal (v-nv)',
  'v-v': 'vocal → vocal (v-v)',
}

const categories = computed(() => {
  const groups = data.value?.groups ?? []
  const order = ['nv-nv', 'nv-v', 'v-nv', 'v-v']
  return order.map((key) => ({
    key,
    label: categoryMeta[key],
    groups: groups.filter((g) => g.category === key),
  }))
})

onMounted(async () => {
  data.value = await fetchDemoGroups()
})
</script>
