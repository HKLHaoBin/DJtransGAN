<template>
  <div ref="el" class="chart" />
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { MixParams } from '@/api'

const props = defineProps<{ params: MixParams | null }>()
const el = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

function render() {
  if (!el.value) return
  if (!chart) chart = echarts.init(el.value, 'dark')
  const p = props.params
  if (!p) {
    chart.clear()
    return
  }
  const series: echarts.SeriesOption[] = []
  for (const [track, data] of Object.entries(p.tracks || {})) {
    if (data.fader?.length) {
      const xs = data.fader_time ?? data.fader.map((_, i) => (i / Math.max(data.fader!.length - 1, 1)) * p.n_time)
      series.push({
        name: `${track} fader`,
        type: 'line',
        showSymbol: false,
        data: xs.map((x, i) => [x, data.fader![i]]),
      })
    }
    data.band?.forEach((curve, bi) => {
      const label = p.band_labels?.[bi] ?? `band ${bi + 1}`
      series.push({
        name: `${track} ${label}`,
        type: 'line',
        showSymbol: false,
        data: curve.map((y, i) => [i, y]),
      })
    })
  }
  chart.setOption(
    {
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      legend: { type: 'scroll', textStyle: { color: '#8b96a8' } },
      grid: { left: 40, right: 20, top: 40, bottom: 30 },
      xAxis: { type: 'value', name: 't / bin', splitLine: { lineStyle: { color: '#2a323e' } } },
      yAxis: { type: 'value', splitLine: { lineStyle: { color: '#2a323e' } } },
      series,
    },
    true,
  )
}

onMounted(() => {
  render()
  window.addEventListener('resize', () => chart?.resize())
})
watch(() => props.params, render, { deep: true })
onBeforeUnmount(() => {
  chart?.dispose()
  chart = null
})
</script>
