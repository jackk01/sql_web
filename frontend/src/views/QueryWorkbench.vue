<template>
  <main class="shell shell-dashboard">
    <section class="hero-board">
      <div class="topbar">
        <div class="hero-title-block">
          <p class="eyebrow">Workspace</p>
          <h1>数据库查询工作台</h1>
          <p class="hero-copy">统一浏览连接、编写只读 SQL、导出结果，保持高效而克制的分析体验。</p>
        </div>
        <div class="user-badge">
          <div class="user-badge-avatar" aria-hidden="true">{{ userInitial }}</div>
          <div class="user-badge-copy">
            <div class="user-badge-row">
              <strong>{{ props.currentUser.display_name }}</strong>
              <span class="user-badge-status">已登录</span>
            </div>
            <span class="user-badge-handle">@{{ props.currentUser.username }}</span>
          </div>
          <el-button class="user-badge-action" text type="primary" @click="$emit('logout')">退出</el-button>
        </div>
      </div>

      <section class="summary-strip">
        <article class="summary-card summary-card-primary summary-card-current">
          <div class="summary-card-head">
            <span class="summary-icon summary-icon-connection" aria-hidden="true">DB</span>
            <span class="summary-label">当前连接</span>
          </div>
          <strong class="summary-value">{{ activeConnection?.name || '未选择' }}</strong>
          <p class="summary-description">
            {{ activeConnection ? `${activeConnection.db_type} · ${activeConnection.host}:${activeConnection.port}` : '请选择一个连接开始查询' }}
          </p>
        </article>
        <article class="summary-card summary-card-database">
          <div class="summary-card-head">
            <span class="summary-icon summary-icon-database" aria-hidden="true">SQL</span>
            <span class="summary-label">数据库</span>
          </div>
          <strong class="summary-value">{{ selectedDatabase || '未选择' }}</strong>
          <p class="summary-description">{{ databases.length }} 个可用库</p>
        </article>
        <ConnectionManager
          v-model="activeConnectionId"
          :connections="connections"
          :db-types="dbTypes"
          @changed="loadConnections"
          @session-expired="emit('session-expired')"
        />
      </section>
    </section>

    <section class="panel workspace-panel">
      <div class="section-heading workbench-heading">
        <div class="section-intro">
          <p class="eyebrow">Query</p>
          <h2>执行 SQL</h2>
          <p class="section-copy">多条 SQL 共存时，默认执行选中语句或光标所在语句。</p>
        </div>
        <div class="toolbar-inline toolbar-surface">
          <div class="toolbar-control">
            <span class="toolbar-label">数据库</span>
            <el-select
              v-model="selectedDatabase"
              placeholder="选择数据库"
              filterable
              clearable
              :disabled="!activeConnectionId"
              @change="handleDatabaseChange"
            >
              <el-option v-for="item in databases" :key="item" :label="item" :value="item" />
            </el-select>
          </div>
          <div class="toolbar-control toolbar-control-limit">
            <span class="toolbar-label">返回行数</span>
            <el-input-number v-model="queryLimit" :min="1" :max="1000" controls-position="right" />
          </div>
          <div class="toolbar-actions">
            <el-button :loading="exporting" :disabled="!activeConnectionId" @click="handleExport">
              导出 Excel
            </el-button>
            <el-button type="primary" :loading="running" :disabled="!activeConnectionId" @click="runQuery">
              运行查询
            </el-button>
          </div>
        </div>
      </div>

      <div class="workbench-grid">
        <aside class="panel panel-soft browser-panel">
          <div class="section-heading compact browser-head">
            <div class="section-intro">
              <p class="eyebrow">Browser</p>
              <h3>库表浏览</h3>
            </div>
            <el-button link :disabled="!activeConnectionId" @click="refreshMetadata">刷新</el-button>
          </div>

          <el-empty v-if="!activeConnectionId" description="选择连接后显示库表" />

          <template v-else>
            <div class="meta-block compact-block">
              <div class="meta-row">
                <span class="meta-title">数据库</span>
                <span class="meta-count">{{ databases.length }}</span>
              </div>
              <el-scrollbar max-height="220px">
                <button
                  v-for="item in databases"
                  :key="item"
                  type="button"
                  class="meta-item"
                  :class="{ active: selectedDatabase === item }"
                  @click="selectedDatabase = item; handleDatabaseChange(item)"
                >
                  {{ item }}
                </button>
              </el-scrollbar>
            </div>

            <div class="meta-block compact-block">
              <div class="meta-row">
                <span class="meta-title">表</span>
                <span class="meta-count">{{ tables.length }}</span>
              </div>
              <el-scrollbar max-height="280px">
                <button
                  v-for="item in tables"
                  :key="item"
                  type="button"
                  class="meta-item"
                  :class="{ active: selectedTable === item }"
                  @click="selectedTable = item"
                >
                  {{ item }}
                </button>
              </el-scrollbar>
            </div>
          </template>
        </aside>

        <section class="panel panel-soft editor-panel">
          <div class="editor-head editor-topline">
            <div class="section-intro">
              <span class="meta-title">SQL 编辑器</span>
              <p class="editor-tip">支持多条 SQL、注释识别、结果导出。</p>
            </div>
            <div class="status-pills">
              <span class="status-pill">{{ queryLimit }} 行限制</span>
              <span v-if="selectedDatabase" class="status-pill active">{{ selectedDatabase }}</span>
              <span v-if="selectedTable" class="status-pill subtle">{{ selectedTable }}</span>
            </div>
          </div>
          <div ref="editorShellRef" class="editor-shell">
            <el-input
              v-model="sql"
              type="textarea"
              :rows="12"
              resize="none"
              placeholder="-- 选中要执行的 SQL，或把光标放在目标语句中&#10;SELECT * FROM your_table LIMIT 20;"
              class="sql-editor"
            />
          </div>

          <div class="result-meta">
            <div class="result-stat-list">
              <span class="result-stat">{{ queryResult ? `${queryResult.row_count} 行` : '未执行' }}</span>
              <span class="result-stat">{{ queryResult ? `${queryResult.elapsed_ms} ms` : '等待查询' }}</span>
              <span v-if="executionHint" class="result-stat">{{ executionHint }}</span>
              <span v-if="queryResult?.truncated" class="result-stat warn">已截断</span>
            </div>
          </div>

          <div class="result-surface">
            <el-table
              v-if="queryResult"
              :data="queryResult.rows"
              border
              stripe
              height="360"
              empty-text="查询没有返回数据"
            >
              <el-table-column
                v-for="column in queryResult.columns"
                :key="column"
                :prop="column"
                :label="column"
                min-width="160"
                show-overflow-tooltip
              />
            </el-table>
            <el-empty v-else description="运行 SQL 后显示结果" />
          </div>
        </section>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'

import { ApiError, executeQuery, exportQuery, getConnections, getDatabaseTypes, getDatabases, getTables } from '../api/client'
import type { ConnectionSummary, DatabaseTypeInfo, QueryResponse, User } from '../api/types'
import ConnectionManager from '../components/ConnectionManager.vue'

const props = defineProps<{
  currentUser: User
}>()

const emit = defineEmits<{
  logout: []
  'session-expired': []
}>()

const dbTypes = ref<DatabaseTypeInfo[]>([])
const connections = ref<ConnectionSummary[]>([])
const activeConnectionId = ref<string | null>(null)
const selectedDatabase = ref<string | null>(null)
const selectedTable = ref<string | null>(null)
const databases = ref<string[]>([])
const tables = ref<string[]>([])
const queryLimit = ref(200)
const running = ref(false)
const exporting = ref(false)
const sql = ref('')
const queryResult = ref<QueryResponse | null>(null)
const editorShellRef = ref<HTMLElement | null>(null)
const executionHint = ref('')

const activeConnection = computed(() =>
  connections.value.find((item) => item.id === activeConnectionId.value) ?? null
)
const userInitial = computed(() => props.currentUser.display_name.trim().charAt(0).toUpperCase() || 'U')

bootstrap()

watch(activeConnectionId, async (connectionId) => {
  queryResult.value = null
  tables.value = []
  databases.value = []
  selectedTable.value = null
  if (!connectionId) {
    selectedDatabase.value = null
    return
  }
  selectedDatabase.value = activeConnection.value?.database ?? null
  await refreshMetadata()
})

async function bootstrap() {
  await Promise.all([loadDbTypes(), loadConnections()])
}

async function loadDbTypes() {
  try {
    dbTypes.value = await getDatabaseTypes()
  } catch (error) {
    handleRequestError(error)
  }
}

async function loadConnections() {
  try {
    connections.value = await getConnections()
    const stillExists = connections.value.some((item) => item.id === activeConnectionId.value)
    if (!stillExists) {
      activeConnectionId.value = connections.value[0]?.id ?? null
    }
  } catch (error) {
    handleRequestError(error)
  }
}

async function refreshMetadata() {
  if (!activeConnectionId.value) {
    return
  }

  try {
    const { items } = await getDatabases(activeConnectionId.value)
    databases.value = items
    if (selectedDatabase.value) {
      await handleDatabaseChange(selectedDatabase.value)
    }
  } catch (error) {
    handleRequestError(error)
  }
}

async function handleDatabaseChange(database: string | null) {
  selectedDatabase.value = database
  tables.value = []
  selectedTable.value = null
  if (!activeConnectionId.value || !database) {
    return
  }

  try {
    const { items } = await getTables(activeConnectionId.value, database)
    tables.value = items
  } catch (error) {
    handleRequestError(error)
  }
}

async function runQuery() {
  if (!activeConnectionId.value) {
    ElMessage.warning('请先选择数据库连接')
    return
  }

  const target = resolveExecutableSql()
  if (!target) {
    return
  }

  running.value = true
  try {
    executionHint.value = target.label
    queryResult.value = await executeQuery({
      connection_id: activeConnectionId.value,
      sql: target.sql,
      database: selectedDatabase.value,
      limit: queryLimit.value,
    })
    ElMessage.success('查询执行完成')
  } catch (error) {
    handleRequestError(error)
  } finally {
    running.value = false
  }
}

async function handleExport() {
  if (!activeConnectionId.value) {
    ElMessage.warning('请先选择数据库连接')
    return
  }

  const target = resolveExecutableSql()
  if (!target) {
    return
  }

  exporting.value = true
  try {
    executionHint.value = `${target.label} · 导出 Excel`
    const { blob, filename } = await exportQuery({
      connection_id: activeConnectionId.value,
      sql: target.sql,
      database: selectedDatabase.value,
      limit: queryLimit.value,
    })
    downloadBlob(blob, filename)
    ElMessage.success('Excel 已开始下载')
  } catch (error) {
    handleRequestError(error)
  } finally {
    exporting.value = false
  }
}

function handleRequestError(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    emit('session-expired')
    return
  }
  ElMessage.error((error as Error).message)
}

function resolveExecutableSql() {
  const textarea = editorShellRef.value?.querySelector('textarea')
  const selectionStart = textarea?.selectionStart ?? 0
  const selectionEnd = textarea?.selectionEnd ?? 0

  if (selectionStart !== selectionEnd) {
    const selectedText = sql.value.slice(selectionStart, selectionEnd)
    const selectedStatements = extractExecutableStatements(selectedText)
    if (selectedStatements.length === 0) {
      ElMessage.warning('选中区域没有可执行的 SQL')
      return null
    }
    if (selectedStatements.length > 1) {
      ElMessage.warning('选中区域包含多条 SQL，请只选择一条')
      return null
    }
    return {
      sql: selectedStatements[0].text,
      label: '执行选中语句',
    }
  }

  const statements = extractExecutableStatements(sql.value)
  if (statements.length === 0) {
    ElMessage.warning('请输入可执行的 SQL')
    return null
  }

  const cursorStatement = findStatementAtCursor(statements, selectionStart)
  if (!cursorStatement) {
    ElMessage.warning('请将光标放在要执行的 SQL 中，或直接选中目标语句')
    return null
  }

  return {
    sql: cursorStatement.text,
    label: '执行当前语句',
  }
}

function findStatementAtCursor(statements: SqlStatement[], cursor: number) {
  const exactMatch = statements.find((statement) => cursor >= statement.start && cursor <= statement.end)
  if (exactMatch) {
    return exactMatch
  }

  const previous = [...statements].reverse().find((statement) => cursor > statement.end)
  if (previous) {
    return previous
  }

  return statements[0] ?? null
}

type SqlStatement = {
  text: string
  start: number
  end: number
}

function extractExecutableStatements(text: string): SqlStatement[] {
  const segments: SqlStatement[] = []
  let start = 0
  let index = 0
  let inSingle = false
  let inDouble = false
  let inBacktick = false
  let inLineComment = false
  let inBlockComment = false

  while (index < text.length) {
    const current = text[index]
    const next = text[index + 1] ?? ''

    if (inLineComment) {
      if (current === '\n') {
        inLineComment = false
      }
      index += 1
      continue
    }

    if (inBlockComment) {
      if (current === '*' && next === '/') {
        inBlockComment = false
        index += 2
      } else {
        index += 1
      }
      continue
    }

    if (!inSingle && !inDouble && !inBacktick) {
      if (current === '-' && next === '-') {
        inLineComment = true
        index += 2
        continue
      }
      if (current === '#') {
        inLineComment = true
        index += 1
        continue
      }
      if (current === '/' && next === '*') {
        inBlockComment = true
        index += 2
        continue
      }
      if (current === ';') {
        pushStatement(segments, text, start, index)
        start = index + 1
        index += 1
        continue
      }
    }

    if (current === "'" && !inDouble && !inBacktick && text[index - 1] !== '\\') {
      inSingle = !inSingle
    } else if (current === '"' && !inSingle && !inBacktick && text[index - 1] !== '\\') {
      inDouble = !inDouble
    } else if (current === '`' && !inSingle && !inDouble) {
      inBacktick = !inBacktick
    }

    index += 1
  }

  pushStatement(segments, text, start, text.length)
  return segments
}

function pushStatement(segments: SqlStatement[], source: string, rawStart: number, rawEnd: number) {
  const rawText = source.slice(rawStart, rawEnd)
  const executableText = stripSqlComments(rawText).trim()
  if (!executableText) {
    return
  }

  const leadingWhitespace = rawText.search(/\S|$/)
  const trailingWhitespaceMatch = /\s*$/.exec(rawText)
  const trailingWhitespace = trailingWhitespaceMatch ? trailingWhitespaceMatch[0].length : 0
  const start = rawStart + leadingWhitespace
  const end = Math.max(start, rawEnd - trailingWhitespace)

  segments.push({
    text: executableText.replace(/;+\s*$/, '').trim(),
    start,
    end,
  })
}

function stripSqlComments(text: string) {
  let result = ''
  let index = 0
  let inSingle = false
  let inDouble = false
  let inBacktick = false
  let inLineComment = false
  let inBlockComment = false

  while (index < text.length) {
    const current = text[index]
    const next = text[index + 1] ?? ''

    if (inLineComment) {
      if (current === '\n') {
        inLineComment = false
        result += current
      }
      index += 1
      continue
    }

    if (inBlockComment) {
      if (current === '*' && next === '/') {
        inBlockComment = false
        index += 2
      } else {
        index += 1
      }
      continue
    }

    if (!inSingle && !inDouble && !inBacktick) {
      if (current === '-' && next === '-') {
        inLineComment = true
        index += 2
        continue
      }
      if (current === '#') {
        inLineComment = true
        index += 1
        continue
      }
      if (current === '/' && next === '*') {
        inBlockComment = true
        index += 2
        continue
      }
    }

    if (current === "'" && !inDouble && !inBacktick && text[index - 1] !== '\\') {
      inSingle = !inSingle
    } else if (current === '"' && !inSingle && !inBacktick && text[index - 1] !== '\\') {
      inDouble = !inDouble
    } else if (current === '`' && !inSingle && !inDouble) {
      inBacktick = !inBacktick
    }

    result += current
    index += 1
  }

  return result
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>
