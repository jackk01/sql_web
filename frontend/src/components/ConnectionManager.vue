<template>
  <section class="panel panel-soft connection-panel">
    <div class="section-heading connection-heading">
      <div class="section-intro">
        <p class="eyebrow">Connections</p>
        <h2>数据库连接</h2>
        <p class="section-copy">选择一个连接进入查询工作台，连接信息只对当前用户可见。</p>
      </div>
      <el-button type="primary" @click="drawerVisible = true">新增连接</el-button>
    </div>

    <el-empty v-if="connections.length === 0" description="还没有连接，先添加一个" />

    <div v-else class="connection-grid">
      <article
        v-for="item in connections"
        :key="item.id"
        class="connection-card"
        :class="{ active: modelValue === item.id }"
        role="button"
        tabindex="0"
        @click="$emit('update:modelValue', item.id)"
        @keydown.enter="$emit('update:modelValue', item.id)"
      >
        <div class="connection-card-top">
          <strong>{{ item.name }}</strong>
          <span class="pill">{{ item.db_type }}</span>
        </div>
        <p class="connection-main">{{ item.host }}:{{ item.port }}</p>
        <p class="connection-sub">{{ item.username }} · {{ item.database || '未指定库' }}</p>
        <div class="connection-card-actions">
          <el-button link type="danger" @click.stop="handleDelete(item.id)">删除</el-button>
        </div>
      </article>
    </div>

    <el-drawer v-model="drawerVisible" title="新增数据库连接" size="440px" class="connection-drawer">
      <el-form label-position="top" :model="form" class="connection-form">
        <el-form-item label="连接名称">
          <el-input v-model="form.name" placeholder="例如：订单库-只读" />
        </el-form-item>
        <el-form-item label="数据库类型">
          <el-select v-model="form.db_type" @change="syncDefaultPort">
            <el-option
              v-for="item in dbTypes"
              :key="item.code"
              :label="item.label"
              :value="item.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="主机地址">
          <el-input v-model="form.host" placeholder="127.0.0.1" />
        </el-form-item>
        <el-form-item label="端口">
          <el-input-number v-model="form.port" :min="1" :max="65535" class="full-width" />
        </el-form-item>
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="readonly_user" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" show-password type="password" />
        </el-form-item>
        <el-form-item label="默认数据库">
          <el-input v-model="form.database" placeholder="可选" />
        </el-form-item>
        <el-form-item v-if="form.db_type === 'clickhouse'" label="安全连接">
          <el-switch v-model="form.secure" />
        </el-form-item>
        <div class="drawer-actions">
          <el-button :loading="testing" @click="handleTest">测试连接</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </div>
      </el-form>
    </el-drawer>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { ApiError, createConnection, deleteConnection, testConnection } from '../api/client'
import type { ConnectionPayload, ConnectionSummary, DatabaseTypeInfo } from '../api/types'

const props = defineProps<{
  modelValue: string | null
  connections: ConnectionSummary[]
  dbTypes: DatabaseTypeInfo[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
  changed: []
  'session-expired': []
}>()

const drawerVisible = ref(false)
const testing = ref(false)
const saving = ref(false)

const form = reactive<ConnectionPayload>({
  name: '',
  db_type: 'mysql',
  host: '',
  port: 3306,
  username: '',
  password: '',
  database: '',
  secure: false,
})

watch(
  () => drawerVisible.value,
  (visible) => {
    if (visible) {
      syncDefaultPort(form.db_type)
    }
  }
)

function syncDefaultPort(dbType: string) {
  const matched = props.dbTypes.find((item) => item.code === dbType)
  if (matched) {
    form.port = matched.default_port
  }
}

function normalizedPayload(): ConnectionPayload {
  return {
    ...form,
    database: form.database?.trim() || null,
  }
}

async function handleTest() {
  testing.value = true
  try {
    const result = await testConnection(normalizedPayload())
    ElMessage.success(`连接成功：${result.driver} ${result.version}`)
  } catch (error) {
    handleRequestError(error)
  } finally {
    testing.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    const saved = await createConnection(normalizedPayload())
    drawerVisible.value = false
    emit('changed')
    emit('update:modelValue', saved.id)
    ElMessage.success('连接已保存')
    resetForm()
  } catch (error) {
    handleRequestError(error)
  } finally {
    saving.value = false
  }
}

async function handleDelete(connectionId: string) {
  try {
    await ElMessageBox.confirm('删除后需要重新录入连接信息，确认继续吗？', '删除连接', {
      type: 'warning',
    })
    await deleteConnection(connectionId)
    if (props.modelValue === connectionId) {
      emit('update:modelValue', null)
    }
    emit('changed')
    ElMessage.success('连接已删除')
  } catch (error) {
    handleRequestError(error)
  }
}

function resetForm() {
  form.name = ''
  form.db_type = 'mysql'
  form.host = ''
  form.port = 3306
  form.username = ''
  form.password = ''
  form.database = ''
  form.secure = false
}

function handleRequestError(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    emit('session-expired')
    return
  }
  if (error instanceof Error && error.message !== 'cancel') {
    ElMessage.error(error.message)
  }
}
</script>
