<template>
  <section class="panel">
    <h1>About</h1>
    <p>
      DJtransGAN 的生成器并不直接合成波形，而是学习如何设置可微的
      <strong>EQ</strong> 与 <strong>fader</strong>，把两首歌在 cue 附近接起来。
    </p>
    <p class="muted">
      过渡分析窗口约 <code>N_TIME = 60</code> 秒（见
      <code>code/djtransgan/config/settings.py</code>）。速度匹配只作用于 Next 的过渡素材，末端回到原速；
      full 输出随后从原始速度的 Next 继续拼接。
    </p>
    <p class="muted">
      论文：Automatic DJ Transitions with Differentiable Audio Effects and Generative Adversarial
      Networks（ICASSP 2022）。
    </p>
  </section>
</template>

<script setup lang="ts"></script>
