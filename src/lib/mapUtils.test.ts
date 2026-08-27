import { describe, expect, it } from 'vitest'
import {
  getVisibleLayer,
  getLatestPrice,
  searchCommunities,
  filterCommunities,
} from './mapUtils'

describe('地图展示层级', () => {
  it('在不同缩放级别切换片区、小区和价格标签', () => {
    expect(getVisibleLayer(11)).toBe('area')
    expect(getVisibleLayer(13)).toBe('community')
    expect(getVisibleLayer(15)).toBe('price')
  })
})

describe('价格快照', () => {
  it('只选择同一口径下最新的有效快照', () => {
    const latest = getLatestPrice([
      { metric: 'listing', value: 12800, capturedAt: '2026-01-01' },
      { metric: 'transaction', value: 11200, capturedAt: '2026-03-01' },
      { metric: 'listing', value: 12500, capturedAt: '2026-03-10' },
    ], 'listing')

    expect(latest?.value).toBe(12500)
  })
})

describe('地图搜索与筛选', () => {
  const communities = [
    { name: '中联天御', plate: '音西板块', tags: ['品质次新'], listingPrice: 17000 },
    { name: '宏路村', plate: '宏路片区', tags: ['低总价'], listingPrice: 5300 },
  ]

  it('按小区名称、片区和标签匹配', () => {
    expect(searchCommunities(communities, '宏路')[0].name).toBe('宏路村')
    expect(filterCommunities(communities, { plate: '音西板块', tag: '品质次新' })).toHaveLength(1)
  })
})
