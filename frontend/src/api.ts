import axios from 'axios'
import type { ReviewData, WorkCreated, RunStatus, RunPage } from './types'

export const createWork = (isbn13: string) =>
  axios.post<WorkCreated>('/api/works', { isbn13 }).then((r) => r.data)

export const getRuns = (page: number) =>
  axios.get<RunPage>('/api/runs', { params: { page } }).then((r) => r.data)

export const getRun = (runId: number) =>
  axios.get<RunStatus>(`/api/runs/${runId}`).then((r) => r.data)

export const getReview = (runId: number) =>
  axios.get<ReviewData>(`/api/runs/${runId}/review`).then((r) => r.data)

export const rejectHeading = (runId: number, fastId: string) =>
  axios.post(`/api/runs/${runId}/decisions`, { fast_id: fastId })

export const undoReject = (runId: number, fastId: string) =>
  axios.delete(`/api/runs/${runId}/decisions/${fastId}`)

export const addHeading = (runId: number, label: string, facet: string) =>
  axios.post(`/api/runs/${runId}/headings`, { label, facet })
