import type { Area, Community, DemoData } from '../types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail ?? `API ${response.status}`)
  return response.json() as Promise<T>
}

export function loadMapData() {
  return request<DemoData>('/api/map')
}

export function importCommunities(communities: Community[]) {
  return request<{ imported: number }>('/api/imports', { method: 'POST', body: JSON.stringify({ communities }) })
}

export function updatePersonal(communityId: string, payload: { note?: string; favorite?: boolean; tags?: string[] }) {
  return request<Community>(`/api/communities/${communityId}/personal`, { method: 'PATCH', body: JSON.stringify(payload) })
}

export function refreshCommunity(communityId: string) {
  return request<{ message: string; status: string }>(`/api/communities/${communityId}/refresh`, { method: 'POST' })
}

export function createArea(area: Area) {
  return request<Area>('/api/areas', { method: 'POST', body: JSON.stringify(area) })
}
