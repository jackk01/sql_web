import type {
  AuthResponse,
  ConnectionPayload,
  ConnectionProfile,
  ConnectionSummary,
  DatabaseTypeInfo,
  LoginPayload,
  QueryPayload,
  QueryResponse,
  RegisterPayload,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

type DownloadResult = {
  blob: Blob
  filename: string
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(normalizeErrorMessage(error.detail, response.statusText), response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

async function requestBlob(url: string, options?: RequestInit): Promise<DownloadResult> {
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      ...(options?.headers ?? {}),
    },
    ...options,
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError(normalizeErrorMessage(error.detail, response.statusText), response.status)
  }

  const blob = await response.blob()
  const filename = parseFilename(response.headers.get('content-disposition'))
  return { blob, filename }
}

function normalizeErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== 'object') {
          return null
        }

        const location = Array.isArray((item as { loc?: unknown }).loc)
          ? ((item as { loc: unknown[] }).loc.slice(1).join('.'))
          : 'field'
        const message = typeof (item as { msg?: unknown }).msg === 'string'
          ? (item as { msg: string }).msg
          : 'Invalid value'
        return `${location}: ${message}`
      })
      .filter(Boolean)

    if (messages.length > 0) {
      return messages.join('；')
    }
  }

  return fallback || 'Request failed'
}

function parseFilename(contentDisposition: string | null): string {
  if (!contentDisposition) {
    return 'query_result.xlsx'
  }

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1])
  }

  const simpleMatch = contentDisposition.match(/filename="?([^"]+)"?/i)
  return simpleMatch?.[1] || 'query_result.xlsx'
}

export function register(payload: RegisterPayload) {
  return request<AuthResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function login(payload: LoginPayload) {
  return request<AuthResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function logout() {
  return request<void>('/api/v1/auth/logout', {
    method: 'POST',
  })
}

export function getCurrentUser() {
  return request<AuthResponse>('/api/v1/auth/me')
}

export function getDatabaseTypes() {
  return request<DatabaseTypeInfo[]>('/api/v1/db-types')
}

export function getConnections() {
  return request<ConnectionSummary[]>('/api/v1/connections')
}

export function getConnection(connectionId: string) {
  return request<ConnectionProfile>(`/api/v1/connections/${connectionId}`)
}

export function createConnection(payload: ConnectionPayload) {
  return request<ConnectionSummary>('/api/v1/connections', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function updateConnection(connectionId: string, payload: ConnectionPayload) {
  return request<ConnectionSummary>(`/api/v1/connections/${connectionId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

export function deleteConnection(connectionId: string) {
  return request<void>(`/api/v1/connections/${connectionId}`, {
    method: 'DELETE',
  })
}

export function testConnection(payload: ConnectionPayload) {
  return request<{ driver: string; version: string }>('/api/v1/connections/test', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getDatabases(connectionId: string) {
  return request<{ items: string[] }>(`/api/v1/connections/${connectionId}/databases`)
}

export function getTables(connectionId: string, database: string) {
  return request<{ items: string[] }>(
    `/api/v1/connections/${connectionId}/tables?database=${encodeURIComponent(database)}`
  )
}

export function executeQuery(payload: QueryPayload) {
  return request<QueryResponse>('/api/v1/query/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function exportQuery(payload: QueryPayload) {
  return requestBlob('/api/v1/query/export', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
}
