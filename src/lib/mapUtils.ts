import { layerZoomConfig } from '../customConfig'

export type MapLayer = 'area' | 'community' | 'price'

export interface PriceSnapshotLike {
  metric: 'listing' | 'transaction'
  value: number
  capturedAt: string
}

export interface CommunityLike {
  name: string
  plate: string
  tags: string[]
  listingPrice: number
}

export interface CommunityFilters {
  plate?: string
  tag?: string
  minPrice?: number
  maxPrice?: number
}

export function getVisibleLayer(zoom: number): MapLayer {
  if (zoom < layerZoomConfig.areaMaxZoom) return 'area'
  if (zoom < layerZoomConfig.communityMaxZoom) return 'community'
  return 'price'
}

export function getLatestPrice<T extends PriceSnapshotLike>(snapshots: T[], metric: PriceSnapshotLike['metric']) {
  return snapshots
    .filter((snapshot) => snapshot.metric === metric && snapshot.value > 0)
    .sort((a, b) => b.capturedAt.localeCompare(a.capturedAt))[0]
}

export function searchCommunities<T extends CommunityLike>(communities: T[], query: string): T[] {
  const normalized = query.trim().toLocaleLowerCase()
  if (!normalized) return communities
  return communities.filter((community) =>
    [community.name, community.plate, ...community.tags]
      .join(' ')
      .toLocaleLowerCase()
      .includes(normalized),
  )
}

export function filterCommunities<T extends CommunityLike>(communities: T[], filters: CommunityFilters): T[] {
  return communities.filter((community) => {
    if (filters.plate && community.plate !== filters.plate) return false
    if (filters.tag && !community.tags.includes(filters.tag)) return false
    if (filters.minPrice !== undefined && community.listingPrice < filters.minPrice) return false
    if (filters.maxPrice !== undefined && community.listingPrice > filters.maxPrice) return false
    return true
  })
}
