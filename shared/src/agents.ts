// Agent data contracts — TypeScript equivalents of backend/app/agents/models.py
// Keep in sync with the Python models.

export type AgentStatus = 'PENDING' | 'RUNNING' | 'DONE' | 'FAILED'

export const AGENT_NAMES = ['flight', 'hotel', 'itinerary', 'budget', 'orchestrator'] as const
export type AgentName = (typeof AGENT_NAMES)[number]

export interface AgentTask {
  task_id: string
  agent_name: AgentName
  destination: string
  start_date: string // ISO YYYY-MM-DD
  end_date: string   // ISO YYYY-MM-DD
  budget: number
  currency: string   // ISO 4217, e.g. "USD"
  raw_request: string
  context: Record<string, unknown>
}

export interface AgentResult {
  task_id: string
  agent_name: AgentName
  status: AgentStatus
  summary: string
  data: Record<string, unknown>
  error: string | null
  duration_ms: number | null
}
