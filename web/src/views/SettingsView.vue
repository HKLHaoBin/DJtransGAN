<template>
  <div>
    <section class="panel" style="margin-bottom: 1rem">
      <h1 style="margin: 0">设置</h1>
      <p class="muted" style="margin: 0.5rem 0 0">
        这里改的是<strong>默认值</strong>，下次打开 Mix 页会带上。每首歌临时要用的开关请直接在 Mix 首页改。
      </p>
    </section>

    <section class="panel" style="margin-bottom: 1rem">
      <h2>预处理 / 变速</h2>
      <label class="check">
        <input v-model="draft.matchBpm" type="checkbox" />
        <span>
          默认匹配 BPM（整轨变速）
          <small class="muted">把 Next 拉到 Prev 的速度；两曲 BPM 差大时 Next 会明显变慢/变快。</small>
        </span>
      </label>
      <label class="check">
        <input v-model="draft.alignCue" type="checkbox" />
        <span>
          默认对齐 cue 窗口长度
          <small class="muted">只拉伸过渡区中段，让两轨 cue 区间一样长；影响比整轨 BPM 匹配小。</small>
        </span>
      </label>
    </section>

    <section class="panel" style="margin-bottom: 1rem">
      <h2>默认 cue</h2>
      <label class="field" style="margin-bottom: 0.75rem">
        Prev cue 方式
        <select v-model="draft.prevCueMode">
          <option value="from_end">从结尾倒数</option>
          <option value="absolute">从开头计时</option>
        </select>
      </label>
      <div class="grid-2">
        <label class="field" v-if="draft.prevCueMode === 'from_end'">
          Prev 默认倒数（秒）
          <input v-model.number="draft.defaultPrevFromEnd" type="number" min="0" step="0.1" />
        </label>
        <label class="field" v-else>
          Prev 默认 cue（秒）
          <input v-model.number="draft.defaultPrevCue" type="number" min="0" step="0.1" />
        </label>
        <label class="field">
          Next 默认 cue（秒，从开头）
          <input v-model.number="draft.defaultNextCue" type="number" min="0" step="0.1" />
        </label>
      </div>
      <p class="muted" style="margin: 0.75rem 0 0; font-size: 0.85rem">
        Prev 切出通常在后半段：选「从结尾倒数」后，上传即可自动落到倒数 30s / 15s 等位置。
      </p>
    </section>

    <section class="panel">
      <div class="row">
        <button class="primary" type="button" @click="save">保存默认值</button>
        <button type="button" @click="reset">恢复出厂</button>
        <span class="status-ok" v-if="savedFlash">已保存</span>
      </div>
      <p class="muted" style="margin: 0.75rem 0 0">
        说明：GAN 仍只在 cue 附近约 60 秒窗口内调 EQ/fader；关闭「匹配 BPM」后两轨保持原速进入混音。
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import {
  DEFAULT_SETTINGS,
  loadSettings,
  saveSettings,
  type StudioSettings,
} from '@/settings'

const draft = reactive<StudioSettings>({ ...loadSettings() })
const savedFlash = ref(false)

function save() {
  saveSettings({ ...draft })
  savedFlash.value = true
  window.setTimeout(() => {
    savedFlash.value = false
  }, 1500)
}

function reset() {
  Object.assign(draft, DEFAULT_SETTINGS)
  save()
}
</script>

<style scoped>
.check {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  margin: 0.85rem 0;
  cursor: pointer;
}
.check input {
  margin-top: 0.35rem;
}
.check span {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.check small {
  font-size: 0.85rem;
}
</style>
