<template>
  <section class="panel">
    <h1>About</h1>
    <p>
      DJtransGAN 的生成器并不直接合成波形，而是学习如何设置可微的
      <strong>EQ</strong> 与 <strong>fader</strong>，把两首歌在 cue 附近接起来。
    </p>
    <p class="muted">
      过渡分析窗口约 <code>N_TIME = 60</code> 秒（见
      <code>code/djtransgan/config/settings.py</code>）。整轨 full 输出是在 short 过渡段前后拼接
      原曲剩余部分。
    </p>
    <p class="muted">
      论文：Automatic DJ Transitions with Differentiable Audio Effects and Generative Adversarial
      Networks（ICASSP 2022）。
    </p>
  </section>
</template>

<script setup lang="ts"></script>
