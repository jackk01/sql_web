export type DatabaseType = 'mysql' | 'clickhouse' | 'starrocks'

export interface User {
  id: number
  username: string
  display_name: string
  created_at: string
  updated_at: string
}

export interface AuthResponse {
  user: User
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload extends LoginPayload {
  display_name: string
}

export interface DatabaseTypeInfo {
  code: DatabaseType
  label: string
  default_port: number
  notes: string
}

export interface ConnectionPayload {
  name: string
  db_type: DatabaseType
  host: string
  port: number
  username: string
  password: string
  database?: string | null
  secure?: boolean
}

export interface ConnectionSummary {
  id: string
  name: string
  db_type: DatabaseType
  host: string
  port: number
  username: string
  database?: string | null
  secure: boolean
  created_at: string
  updated_at: string
}

export interface QueryPayload {
  connection_id: string
  sql: string
  database?: string | null
  limit?: number
}

export interface QueryResponse {
  columns: string[]
  rows: Record<string, unknown>[]
  row_count: number
  truncated: boolean
  elapsed_ms: number
}
