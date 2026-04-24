<template>
  <div v-if="bootstrapping" class="shell">
    <section class="panel auth-card">
      <p class="eyebrow">SQL Web Console</p>
      <h1>正在初始化工作台</h1>
      <p class="hero-copy">检查登录状态并准备你的个人查询空间。</p>
    </section>
  </div>

  <AuthShell v-else-if="!currentUser" @authenticated="handleAuthenticated" />

  <QueryWorkbench
    v-else
    :current-user="currentUser"
    @logout="handleLogout"
    @session-expired="handleSessionExpired"
  />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'

import AuthShell from './components/AuthShell.vue'
import { ApiError, getCurrentUser, logout } from './api/client'
import type { User } from './api/types'
import QueryWorkbench from './views/QueryWorkbench.vue'

const bootstrapping = ref(true)
const currentUser = ref<User | null>(null)

onMounted(async () => {
  try {
    const response = await getCurrentUser()
    currentUser.value = response.user
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) {
      ElMessage.error((error as Error).message)
    }
  } finally {
    bootstrapping.value = false
  }
})

function handleAuthenticated(user: User) {
  currentUser.value = user
}

async function handleLogout() {
  try {
    await logout()
  } finally {
    currentUser.value = null
  }
}

function handleSessionExpired() {
  currentUser.value = null
  ElMessage.warning('登录状态已失效，请重新登录')
}
</script>
