<template>
  <section class="connection-inline">
    <button type="button" class="summary-card connection-card connection-card-add" @click="openCreateDialog">
      <span class="summary-label">数据库连接</span>
      <strong>新增连接</strong>
      <span>创建一个新的数据库配置</span>
    </button>

    <article v-if="connections.length === 0" class="summary-card connection-card connection-card-empty">
      <span class="summary-label">数据库连接</span>
      <strong>还没有连接</strong>
      <span>点击左侧新增连接开始配置</span>
    </article>

    <template v-else>
      <article
        v-for="item in connections"
        :key="item.id"
        class="summary-card connection-card"
        :class="{ active: modelValue === item.id }"
        role="button"
        tabindex="0"
        @click="openEditDialog(item.id)"
        @keydown.enter="openEditDialog(item.id)"
      >
        <span class="summary-label">数据库连接</span>
        <div class="connection-card-top">
          <strong>{{ item.name }}</strong>
          <span class="pill">{{ item.db_type }}</span>
        </div>
        <span class="connection-card-host">{{ item.host }}:{{ item.port }}</span>
        <span class="connection-card-meta">{{ item.username }} · {{ item.database || '未指定库' }}</span>
        <div class="connection-card-actions">
          <el-button link type="primary" @click.stop="$emit('update:modelValue', item.id)">
            {{ modelValue === item.id ? '当前连接' : '使用' }}
          </el-button>
          <el-button link @click.stop="openEditDialog(item.id)">编辑</el-button>
          <el-button link type="danger" @click.stop="handleDelete(item.id)">删除</el-button>
        </div>
      </article>
    </template>

    <el-dialog
      v-model="dialogVisible"
      width="520px"
      align-center
      class="connection-dialog"
      modal-class="connection-dialog-overlay"
      :title="dialogTitle"
    >
      <div class="connection-dialog-copy">
        <p>{{ dialogDescription }}</p>
      </div>
      <el-skeleton :loading="dialogLoading" animated :rows="8">
        <template #default>
          <el-form label-position="top" :model="form" class="connection-form connection-form-dialog">
            <section class="connection-form-section connection-form-section-primary">
              <div class="connection-form-section-head">
                <span class="connection-form-section-kicker">常用信息</span>
                <strong>先填写最常修改的连接信息</strong>
              </div>
              <div class="connection-form-grid">
                <el-form-item label="连接名称" class="connection-form-span-2">
                  <el-input v-model="form.name" placeholder="例如：订单库-只读" />
                </el-form-item>
                <el-form-item label="主机地址" class="connection-form-span-2">
                  <el-input v-model="form.host" placeholder="127.0.0.1" />
                </el-form-item>
                <el-form-item label="用户名">
                  <el-input v-model="form.username" placeholder="readonly_user" />
                </el-form-item>
                <el-form-item label="密码">
                  <el-input v-model="form.password" show-password type="password" />
                </el-form-item>
              </div>
            </section>

            <section class="connection-form-section">
              <div class="connection-form-section-head">
                <span class="connection-form-section-kicker">连接参数</span>
                <strong>补充协议、端口和默认库</strong>
              </div>
              <div class="connection-form-grid">
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
                <el-form-item label="端口">
                  <el-input-number v-model="form.port" :min="1" :max="65535" class="full-width" />
                </el-form-item>
                <el-form-item label="默认数据库" class="connection-form-span-2">
                  <el-input v-model="form.database" placeholder="可选" />
                </el-form-item>
                <el-form-item v-if="form.db_type === 'clickhouse'" label="安全连接" class="connection-form-span-2">
                  <div class="connection-switch-row">
                    <el-switch v-model="form.secure" />
                    <span class="connection-switch-copy">通过 HTTPS 访问 ClickHouse</span>
                  </div>
                </el-form-item>
              </div>
            </section>
            <div class="dialog-actions">
              <el-button @click="handleCancel">取消</el-button>
              <el-button :loading="testing" :disabled="dialogLoading" @click="handleTest">测试连接</el-button>
              <el-button type="primary" :loading="saving" :disabled="dialogLoading" @click="handleSave">
                {{ submitLabel }}
              </el-button>
            </div>
          </el-form>
        </template>
      </el-skeleton>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import {
  ApiError,
  createConnection,
  deleteConnection,
  getConnection,
  testConnection,
  updateConnection,
} from '../api/client'
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

const dialogVisible = ref(false)
const editingConnectionId = ref<string | null>(null)
const dialogLoading = ref(false)
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

const dialogTitle = computed(() => editingConnectionId.value ? '编辑数据库连接' : '新增数据库连接')
const dialogDescription = computed(() => (
  editingConnectionId.value
    ? '点击已配置连接即可修改信息，保存后会覆盖当前配置。'
    : '用一个独立表单填写连接信息，保存后会立即出现在当前连接列表中。'
))
const submitLabel = computed(() => editingConnectionId.value ? '保存修改' : '保存')

watch(
  () => dialogVisible.value,
  (visible) => {
    if (visible) {
      if (!editingConnectionId.value) {
        syncDefaultPort(form.db_type)
      }
      return
    }
    if (!saving.value && !testing.value) {
      editingConnectionId.value = null
      dialogLoading.value = false
      resetForm()
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
    const payload = normalizedPayload()
    const editingId = editingConnectionId.value
    const saved = editingId
      ? await updateConnection(editingId, payload)
      : await createConnection(payload)
    dialogVisible.value = false
    emit('changed')
    emit('update:modelValue', saved.id)
    ElMessage.success(editingId ? '连接信息已更新' : '连接已保存')
    resetForm()
  } catch (error) {
    handleRequestError(error)
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  dialogVisible.value = false
}

function openCreateDialog() {
  editingConnectionId.value = null
  dialogLoading.value = false
  resetForm()
  dialogVisible.value = true
}

async function openEditDialog(connectionId: string) {
  editingConnectionId.value = connectionId
  dialogVisible.value = true
  dialogLoading.value = true
  try {
    const profile = await getConnection(connectionId)
    form.name = profile.name
    form.db_type = profile.db_type
    form.host = profile.host
    form.port = profile.port
    form.username = profile.username
    form.password = profile.password
    form.database = profile.database || ''
    form.secure = profile.secure
  } catch (error) {
    dialogVisible.value = false
    handleRequestError(error)
  } finally {
    dialogLoading.value = false
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
