<template>
  <div class="layout">
    <nav class="nav">
      <div class="brand">DJtransGAN <span>Mix Studio</span></div>
      <RouterLink to="/">Mix</RouterLink>
      <RouterLink to="/results">结果</RouterLink>
      <RouterLink to="/settings">设置</RouterLink>
      <RouterLink to="/demo">Demo</RouterLink>
      <RouterLink to="/about">About</RouterLink>
    </nav>
    <RouterView />
  </div>
</template>

<script setup lang="ts">
</script>
