export interface WorkCreated {
  work_id: number
  run_id: number
  status: string
}

export interface RunStatus {
  id: number
  status: string
  error: string | null
}

export interface Heading {
  id: number
  proposed_label: string
  label: string | null
  fast_id: string | null
  facet: string
  tier: string
  source_model: string
  position: number
}

export interface FinalEntry {
  fast_id: string
  label: string | null
  facet: string
  source_models: string[]
  rejected: boolean
}

export interface ReviewData {
  isbn13: string
  title: string | null
  description: string | null
  metadata_source: string | null
  run_id: number
  status: string
  proposals: Record<string, Heading[]>
  final: FinalEntry[]
}

// one row of the history table (GET /api/runs)
export interface RunListItem {
  id: number
  status: string
  created_at: string
  work_id: number
  isbn13: string
  title: string | null
}

export interface RunPage {
  items: RunListItem[]
  total: number
  page: number
  page_size: number
}
