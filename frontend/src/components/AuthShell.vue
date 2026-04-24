<template>
  <main class="shell auth-shell">
    <section class="auth-backdrop">
      <div class="auth-orbit auth-orbit-one"></div>
      <div class="auth-orbit auth-orbit-two"></div>
      <section class="panel auth-card">
        <div class="section-heading auth-head">
          <div class="section-intro">
            <p class="eyebrow">内部数据库查询平台</p>
            <h1>登录后只管理自己的连接配置</h1>
            <p class="hero-copy">面向内部团队的统一查询入口，保持连接隔离、只读执行与导出能力。</p>
          </div>
          <span class="pill">SQLite + Session</span>
        </div>

        <el-tabs v-model="activeTab" class="auth-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form label-position="top" :model="loginForm" class="auth-form">
              <el-form-item label="用户名">
                <el-input v-model="loginForm.username" placeholder="例如：alice 或 alice@example.com" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="loginForm.password" type="password" show-password />
              </el-form-item>
              <el-button type="primary" :loading="submitting" class="auth-submit" @click="handleLogin">
                登录并进入系统
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form label-position="top" :model="registerForm" class="auth-form">
              <el-form-item label="展示名称">
                <el-input v-model="registerForm.display_name" placeholder="例如：张三" />
              </el-form-item>
              <el-form-item label="用户名">
                <el-input
                  v-model="registerForm.username"
                  placeholder="支持字母、数字、点、下划线、中划线、@"
                />
              </el-form-item>
              <el-form-item label="密码">
                <el-input v-model="registerForm.password" type="password" show-password />
              </el-form-item>
              <el-button type="primary" :loading="submitting" class="auth-submit" @click="handleRegister">
                注册并创建个人空间
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </section>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

import { login, register } from '../api/client'
import type { LoginPayload, RegisterPayload, User } from '../api/types'

const emit = defineEmits<{
  authenticated: [user: User]
}>()

const activeTab = ref<'login' | 'register'>('login')
const submitting = ref(false)

const loginForm = reactive<LoginPayload>({
  username: '',
  password: '',
})

const registerForm = reactive<RegisterPayload>({
  display_name: '',
  username: '',
  password: '',
})

async function handleLogin() {
  const validationError = validateLogin()
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }

  submitting.value = true
  try {
    const response = await login(loginForm)
    emit('authenticated', response.user)
    ElMessage.success(`欢迎回来，${response.user.display_name}`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    submitting.value = false
  }
}

async function handleRegister() {
  const validationError = validateRegister()
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }

  submitting.value = true
  try {
    const response = await register(registerForm)
    emit('authenticated', response.user)
    ElMessage.success(`注册成功，欢迎 ${response.user.display_name}`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    submitting.value = false
  }
}

function validateLogin() {
  if (!registerLikeUsername(loginForm.username)) {
    return '用户名至少 3 位，只支持字母、数字、点、下划线、中划线、@'
  }
  if ((loginForm.password ?? '').length < 8) {
    return '密码至少需要 8 位'
  }
  return ''
}

function validateRegister() {
  if ((registerForm.display_name ?? '').trim().length < 2) {
    return '展示名称至少需要 2 个字符'
  }
  if (!registerLikeUsername(registerForm.username)) {
    return '用户名至少 3 位，只支持字母、数字、点、下划线、中划线、@'
  }
  if ((registerForm.password ?? '').length < 8) {
    return '密码至少需要 8 位'
  }
  return ''
}

function registerLikeUsername(value: string) {
  return /^[a-zA-Z0-9_.@-]{3,50}$/.test((value ?? '').trim())
}
</script>
