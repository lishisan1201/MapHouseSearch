export type Coordinate = [number, number]
export type MapLayer = 'area' | 'community' | 'price'
export type BaseMapType = 'normal' | '3d' | 'satellite'
export type PoiCategory = 'hospital' | 'school' | 'mall' | 'transit' | 'park'
export type PriceMetric = 'listing' | 'transaction'


export interface PriceSnapshot {
  metric: PriceMetric
  value: number
  capturedAt: string
}

export interface Community {
  id: string
  name: string
  plate: string
  center: Coordinate
  listingPrice: number
  transactionPrice: number
  listingCount: number
  buildYear: number
  developer: string
  propertyCompany: string
  tags: string[]
  lastUpdated: string
  source: string
  note: string
  favorite: boolean
  snapshots: PriceSnapshot[]
}

export interface Area {
  id: string
  name: string
  type: 'plate' | 'custom'
  color: string
  minZoom: number
  maxZoom: number
  center: Coordinate
  polygon: Coordinate[]
}

export interface Poi {
  id: string
  name: string
  category: PoiCategory
  center: Coordinate
  subtitle: string
}

export interface DemoData {
  areas: Area[]
  communities: Community[]
  pois: Poi[]
}

export const poiCategoryLabels: Record<PoiCategory, string> = {
  hospital: '医院',
  school: '学校',
  mall: '商圈',
  transit: '交通',
  park: '公园',
}
