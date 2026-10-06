import type { Project, ProjectSummary, Ruleset } from './types'

const jsonHeaders = { 'Content-Type': 'application/json' }

export class ApiError extends Error {
  constructor(message: string, public status: number, public payload: unknown) { super(message) }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }))
    throw new ApiError((payload as { detail?: string }).detail ?? 'Request failed', response.status, payload)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  projects: () => request<ProjectSummary[]>('/api/projects'),
  project: (id: string) => request<Project>(`/api/projects/${id}`),
  createProject: (body: { name: string; description?: string }) => request<Project>('/api/projects', { method: 'POST', headers: jsonHeaders, body: JSON.stringify(body) }),
  rulesets: () => request<Ruleset[]>('/api/rulesets'),
  createFunction: (projectId: string, body: object) => request<Project>(`/api/projects/${projectId}/functions`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify(body) }),
  previewComponent: (projectId: string, body: object) => request<{ designation: string; valid: boolean; issues: unknown[] }>(`/api/projects/${projectId}/components/preview`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify(body) }),
  createComponent: (projectId: string, body: object) => request(`/api/projects/${projectId}/components`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify(body) }),
  updateComponent: (componentId: string, body: object) => request(`/api/components/${componentId}`, { method: 'PATCH', headers: jsonHeaders, body: JSON.stringify(body) }),
  deleteComponent: (componentId: string) => request(`/api/components/${componentId}`, { method: 'DELETE' }),
  duplicateComponent: (componentId: string) => request(`/api/components/${componentId}/duplicate`, { method: 'POST' }),
  bulkComponents: (projectId: string, componentIds: string[], changes: object) => request(`/api/projects/${projectId}/components/bulk`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify({ component_ids: componentIds, changes }) }),
  createRelation: (projectId: string, body: object) => request(`/api/projects/${projectId}/relations`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify(body) }),
  deleteRelation: (relationId: string) => request(`/api/relations/${relationId}`, { method: 'DELETE' }),
  validate: (projectId: string) => request<{ issues: unknown[] }>(`/api/projects/${projectId}/validate`, { method: 'POST' }),
  undo: (projectId: string) => request<Project>(`/api/projects/${projectId}/undo`, { method: 'POST' }),
  redo: (projectId: string) => request<Project>(`/api/projects/${projectId}/redo`, { method: 'POST' }),
  history: (componentId: string) => request<Record<string, unknown>[]>(`/api/components/${componentId}/history`),
  explanation: (componentId: string) => request<{ summary: string }>(`/api/components/${componentId}/explanation`),
  graph: (projectId: string) => request<{ nodes: { id: string; type: string; label: string }[]; edges: { id: string; source: string; target: string; kind: string; label?: string }[] }>(`/api/projects/${projectId}/graph`),
  infer: (projectId: string, text: string) => request<{ query_id: string; candidates: import('./types').Candidate[] }>(`/api/projects/${projectId}/inference`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify({ text }) }),
  approve: (queryId: string, decisions: object[]) => request(`/api/inference/${queryId}/approve`, { method: 'POST', headers: jsonHeaders, body: JSON.stringify({ decisions }) }),
}
