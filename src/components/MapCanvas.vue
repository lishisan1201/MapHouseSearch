<template>
  <div ref="mapContainer" class="map-canvas">
    <div v-if="!isAmapReady" class="map-blocked-state">
      <div v-if="isLoading" class="blocked-card loading-card">
        <Loader2 class="spinner" :size="32" />
        <h3>正在加载高德地图...</h3>
        <p>正在初始化高德地图 JS API 2.0 引擎</p>
      </div>
      <div v-else class="blocked-card error-card">
        <div class="blocked-icon">
          <KeyRound v-if="!hasKey" :size="28" />
          <AlertTriangle v-else :size="28" />
        </div>
        <h2>{{ !hasKey ? '未配置高德地图 API Key' : '高德地图加载失败' }}</h2>
        <p class="blocked-intro">
          本项目已禁用离线示意底图，必须配置高德地图 JS API Key 方可正常使用。
        </p>

        <div v-if="errorMessage" class="error-detail-box">
          <strong>错误原因：</strong>
          <span>{{ errorMessage }}</span>
        </div>

        <div class="config-guide">
          <div class="guide-step">
            <span class="step-num">1</span>
            <span>前往 <a href="https://console.amap.com/" target="_blank" rel="noopener noreferrer">高德开放平台控制台</a> 创建应用，添加 Key（<strong>服务平台务必选择「Web端 (JS API)」</strong>）。</span>
          </div>
          <div class="guide-step">
            <span class="step-num">2</span>
            <span>在项目根目录的 <code>.env</code> 文件中配置 Key 与安全密钥：</span>
          </div>
          <pre class="code-box"><code>VITE_AMAP_KEY=你的高德Web端Key
VITE_AMAP_SECURITY_CODE=你的安全密钥</code></pre>
          <div class="guide-step">
            <span class="step-num">3</span>
            <span>保存 <code>.env</code> 文件后，<strong>重启前端开发服务器</strong>（重新执行 <code>npm run dev</code>）。</span>
          </div>
        </div>

        <button class="button primary retry-btn" type="button" @click="loadAmap">
          <RefreshCw :size="15" /> 重新尝试加载地图
        </button>
      </div>
    </div>

    <div class="amap-host"></div>
    <div v-if="isAmapReady" class="map-status">
      <span class="status-dot"></span>高德地图 2.0 ({{ baseMapLabel }})<span class="status-divider">·</span>{{ zoom.toFixed(1) }} 级
    </div>
    <div v-if="isAmapReady" class="map-attribution">GCJ-02 坐标系</div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { AlertTriangle, KeyRound, Loader2, RefreshCw, X } from 'lucide-vue-next'
import { load as loadAmapApi } from '@amap/amap-jsapi-loader'
import type { Area, BaseMapType, Community, Coordinate, MapLayer, Poi, PoiCategory } from '../types'
import {
  lifeCircleConfig,
  mapThemeConfig,
  markerThemeConfig,
  poiCategoryColors,
  viewportScanConfig,
} from '../customConfig'

export interface DiscoveredCommunity {
  id: string
  name: string
  center: Coordinate
  address: string
  type: string
}

const props = withDefaults(
  defineProps<{
    areas: Area[]
    communities: Community[]
    pois: Poi[]
    zoom: number
    selectedId?: string
    layer: MapLayer
    baseMapType?: BaseMapType
    enableViewportScan?: boolean
    showCommunityNames: boolean
    showPrices: boolean
    showPois: boolean
    drawMode: boolean
    drawPoints: Coordinate[]
  }>(),
  {
    baseMapType: 'normal',
    enableViewportScan: true,
  },
)

const emit = defineEmits<{
  (event: 'select', id: string): void
  (event: 'area-select', id: string): void
  (event: 'poi-select', id: string): void
  (event: 'zoom-change', value: number): void
  (event: 'draw-point', value: Coordinate): void
  (event: 'discovered-scan', count: number): void
}>()

const mapContainer = ref<HTMLElement | null>(null)
const isAmapReady = ref(false)
const isLoading = ref(true)
const errorMessage = ref('')
const hasKey = computed(() => Boolean(import.meta.env.VITE_AMAP_KEY))
const discoveredCount = ref(0)

const baseMapLabel = computed(() => {
  const map: Record<BaseMapType, string> = {
    normal: '标准全彩',
    '3d': '3D立体',
    satellite: '卫星影像',
  }
  return map[props.baseMapType] || '标准全彩'
})

let mapInstance: any = null
let amapApi: any = null
let amapOverlays: any[] = []
let circleOverlays: any[] = []
let boundaryOverlays: any[] = []
let discoveredMarkers: any[] = []
let satelliteLayer: any = null
let roadNetLayer: any = null
let placeSearchInstance: any = null
let scanPlaceSearchInstance: any = null
let geocoderInstance: any = null
let infoWindowInstance: any = null
let scanDebounceTimer: any = null
const discoveredCommunities = ref<DiscoveredCommunity[]>([])

function formatWan(price: number) {
  return `${(price / 10000).toFixed(2)}万`
}

function poiBadge(category: PoiCategory) {
  return poiCategoryColors[category]?.badge || '标'
}

async function loadAmap() {
  const key = import.meta.env.VITE_AMAP_KEY
  const securityCode = import.meta.env.VITE_AMAP_SECURITY_CODE

  if (!key) {
    isLoading.value = false
    isAmapReady.value = false
    errorMessage.value = '未在 .env 中检测到 VITE_AMAP_KEY。请配置有效的 Key 并重启 Vite 开发服务器。'
    return
  }

  if (securityCode) {
    window._AMapSecurityConfig = { securityJsCode: securityCode }
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    amapApi = await loadAmapApi({
      key,
      version: '2.0',
      plugins: ['AMap.Scale', 'AMap.ToolBar', 'AMap.PlaceSearch', 'AMap.Geocoder', 'AMap.DistrictSearch'],
    })

    await nextTick()
    if (!mapContainer.value || !amapApi) {
      isLoading.value = false
      return
    }

    const host = mapContainer.value.querySelector('.amap-host') as HTMLElement
    if (!host) {
      isLoading.value = false
      return
    }

    if (mapInstance) {
      mapInstance.destroy()
      mapInstance = null
    }

    mapInstance = new amapApi.Map(host, {
      zoom: props.zoom,
      center: [119.383, 25.72],
      zooms: [10, 18],
      viewMode: '3D',
      pitch: props.baseMapType === '3d' ? 52 : 0,
      mapStyle: 'amap://styles/normal',
      isHotspot: true,
    })

    // 获取福清市官方行政区划边界并应用反向遮罩（受 mapThemeConfig.enableDistrictMask 控制）
    if (mapThemeConfig.enableDistrictMask && amapApi.DistrictSearch) {
      const districtSearch = new amapApi.DistrictSearch({
        subdistrict: 0,
        extensions: 'all',
        level: 'city',
      })
      districtSearch.search('福清市', (status: string, result: any) => {
        if (status === 'complete' && result?.districtList?.length) {
          const boundaries = result.districtList[0].boundaries || []
          if (boundaries.length && mapInstance) {
            // 外围大矩形包裹区
            const outerRing = [
              new amapApi.LngLat(60, 0),
              new amapApi.LngLat(140, 0),
              new amapApi.LngLat(140, 60),
              new amapApi.LngLat(60, 60),
            ]
            // 反向遮罩多边形（外围实心遮蔽，福清市内镂空透明）
            const maskPolygon = new amapApi.Polygon({
              path: [outerRing, ...boundaries],
              fillColor: mapThemeConfig.maskFillColor,
              fillOpacity: mapThemeConfig.maskFillOpacity,
              strokeColor: mapThemeConfig.districtBorderColor,
              strokeWeight: mapThemeConfig.districtBorderWeight,
              strokeOpacity: mapThemeConfig.districtBorderOpacity,
              zIndex: 3,
              bubble: true,
            })
            mapInstance.add(maskPolygon)
          }
        }
      })
    }

    if (amapApi.PlaceSearch) {
      placeSearchInstance = new amapApi.PlaceSearch({
        city: '福清',
        citylimit: false,
        extensions: 'all',
      })
      scanPlaceSearchInstance = new amapApi.PlaceSearch({
        city: '福清',
        type: viewportScanConfig.types,
        pageSize: viewportScanConfig.pageSize,
        extensions: 'base',
      })
    }

    if (amapApi.Geocoder) {
      geocoderInstance = new amapApi.Geocoder({
        city: '福清',
      })
    }

    satelliteLayer = new amapApi.TileLayer.Satellite()
    roadNetLayer = new amapApi.TileLayer.RoadNet()

    mapInstance.on('complete', () => {
      console.log('[AMap] 地图渲染就绪')
      scanViewportCommunities()
    })
    mapInstance.on('zoomend', () => {
      emit('zoom-change', mapInstance.getZoom())
      scanViewportCommunities()
    })
    mapInstance.on('moveend', () => {
      scanViewportCommunities()
    })
    mapInstance.on('click', (event: any) => {
      if (props.drawMode) {
        emit('draw-point', [event.lnglat.getLng(), event.lnglat.getLat()])
        return
      }

      const clickedLngLat: Coordinate = [event.lnglat.getLng(), event.lnglat.getLat()]

      if (event.poi) {
        // 点击了高德底图自带 POI / 建筑物
        const poiName = event.poi.name || '选定地点'
        const poiLocation: Coordinate = event.poi.location
          ? [event.poi.location.getLng(), event.poi.location.getLat()]
          : clickedLngLat

        // 判断是否为已有整理小区
        const matched = props.communities.find(
          (c) => c.name === poiName || poiName.includes(c.name) || c.name.includes(poiName),
        )
        if (matched) {
          emit('select', matched.id)
        } else {
          showLocationAnalysis(poiName, poiLocation, false)
        }
      } else {
        // 点击了地图任意坐标空白处
        if (geocoderInstance) {
          geocoderInstance.getAddress(clickedLngLat, (status: string, result: any) => {
            let placeName = '地图选定位置'
            if (status === 'complete' && result?.regeocode) {
              const aois = result.regeocode.aois
              const pois = result.regeocode.pois
              if (aois && aois.length) {
                placeName = aois[0].name
              } else if (pois && pois.length) {
                placeName = pois[0].name
              } else if (result.regeocode.formattedAddress) {
                placeName = result.regeocode.formattedAddress.replace(/^福建省福州市福清市/, '') || '地图选定位置'
              }
            }
            showLocationAnalysis(placeName, clickedLngLat, false)
          })
        } else {
          showLocationAnalysis('地图选定位置', clickedLngLat, false)
        }
      }
    })

    isAmapReady.value = true
    isLoading.value = false

    updateBaseMap()
    renderAmap()
    if (props.selectedId) {
      renderSelectedEffects()
    }

    await nextTick()
    mapInstance?.resize()
    setTimeout(() => {
      mapInstance?.resize()
      scanViewportCommunities()
    }, 100)
  } catch (err: any) {
    console.error('高德地图加载或初始化失败:', err)
    isAmapReady.value = false
    isLoading.value = false
    const msg = err?.message || String(err)
    if (msg.includes('INVALID_USER_KEY') || msg.includes('USERKEY_PLAT_NOMATCH') || msg.includes('USER_KEY_RECYCLED')) {
      errorMessage.value = `高德鉴权失败 (${msg})。请检查 Key 是否为「Web端 (JS API)」类型，且安全密钥 (Security Code) 是否匹配。`
    } else {
      errorMessage.value = msg || '高德地图加载失败，请检查网络连接与控制台报错。'
    }
  }
}

function scanViewportCommunities() {
  if (!mapInstance || !amapApi || !isAmapReady.value || !props.enableViewportScan || !scanPlaceSearchInstance) return
  const currentZoom = mapInstance.getZoom()
  if (currentZoom < viewportScanConfig.minZoom) {
    clearDiscoveredMarkers()
    discoveredCommunities.value = []
    discoveredCount.value = 0
    emit('discovered-scan', 0)
    return
  }

  clearTimeout(scanDebounceTimer)
  scanDebounceTimer = setTimeout(() => {
    const bounds = mapInstance.getBounds()
    if (!bounds) return

    scanPlaceSearchInstance.searchInBounds('', bounds, (status: string, result: any) => {
      if (status === 'complete' && result?.poiList?.pois?.length) {
        const curatedNames = new Set(props.communities.map((c) => c.name))
        const list: DiscoveredCommunity[] = []

        result.poiList.pois.forEach((poi: any) => {
          if (!poi.location) return
          const isCurated = curatedNames.has(poi.name) || props.communities.some((c) => c.name.includes(poi.name) || poi.name.includes(c.name))
          if (!isCurated) {
            list.push({
              id: poi.id,
              name: poi.name,
              center: [poi.location.getLng(), poi.location.getLat()],
              address: poi.address || '',
              type: poi.type || '住宅小区',
            })
          }
        })

        discoveredCommunities.value = list
        discoveredCount.value = list.length
        emit('discovered-scan', list.length)
        renderDiscoveredMarkers()
      }
    })
  }, viewportScanConfig.debounceMs)
}

function clearDiscoveredMarkers() {
  if (discoveredMarkers.length && mapInstance) {
    mapInstance.remove(discoveredMarkers)
    discoveredMarkers = []
  }
}

function renderDiscoveredMarkers() {
  clearDiscoveredMarkers()
  if (!mapInstance || !amapApi || !props.showCommunityNames || !props.enableViewportScan) return

  discoveredCommunities.value.forEach((c) => {
    const isSelected = props.selectedId === c.id
    const marker = new amapApi.Marker({
      position: c.center,
      content: `
        <button type="button" class="amap-discovered-marker ${isSelected ? 'active-selected' : ''}" title="${c.name} (${c.address})">
          <span class="disc-dot"></span>
          <span class="disc-name">${c.name}</span>
        </button>
      `,
      offset: new amapApi.Pixel(-24, -14),
      zIndex: isSelected ? 90 : 25,
    })

    marker.on('click', () => {
      showLocationAnalysis(c.name, c.center, false)
    })

    discoveredMarkers.push(marker)
  })

  mapInstance.add(discoveredMarkers)
}

function updateBaseMap() {
  if (!mapInstance || !amapApi || !isAmapReady.value) return
  if (!satelliteLayer || !roadNetLayer) {
    satelliteLayer = new amapApi.TileLayer.Satellite()
    roadNetLayer = new amapApi.TileLayer.RoadNet()
  }

  if (props.baseMapType === 'satellite') {
    mapInstance.setPitch(0)
    mapInstance.setRotation(0)
    if (mapInstance.setFeatures) {
      mapInstance.setFeatures(['bg', 'road', 'point'])
    }
    mapInstance.add([satelliteLayer, roadNetLayer])
  } else if (props.baseMapType === '3d') {
    mapInstance.remove([satelliteLayer, roadNetLayer])
    if (mapInstance.setFeatures) {
      mapInstance.setFeatures(['bg', 'road', 'building', 'point'])
    }
    mapInstance.setMapStyle('amap://styles/normal')
    mapInstance.setPitch(52)
    mapInstance.setRotation(0)
  } else {
    mapInstance.remove([satelliteLayer, roadNetLayer])
    if (mapInstance.setFeatures) {
      mapInstance.setFeatures(['bg', 'road', 'building', 'point'])
    }
    mapInstance.setMapStyle('amap://styles/normal')
    mapInstance.setPitch(0)
    mapInstance.setRotation(0)
  }
}

let isProgrammaticClosing = false
const activeLocationAnalysis = ref<{ name: string; center: Coordinate; isCurated: boolean } | null>(null)

function handleClearAnalysis() {
  clearSelectedEffects()
  emit('select', '')
}

function clearSelectedEffects() {
  activeLocationAnalysis.value = null
  if (!mapInstance) return
  if (circleOverlays.length) {
    mapInstance.remove(circleOverlays)
    circleOverlays = []
  }
  if (boundaryOverlays.length) {
    mapInstance.remove(boundaryOverlays)
    boundaryOverlays = []
  }
  if (infoWindowInstance) {
    isProgrammaticClosing = true
    infoWindowInstance.close()
    setTimeout(() => {
      isProgrammaticClosing = false
    }, 60)
  }
}

function showLocationAnalysis(name: string, center: Coordinate, isCustomCommunity: boolean) {
  // 方式5：重复点击同一地点时，自动切换关闭生活圈
  if (
    activeLocationAnalysis.value &&
    activeLocationAnalysis.value.name === name &&
    Math.abs(activeLocationAnalysis.value.center[0] - center[0]) < 0.0001 &&
    Math.abs(activeLocationAnalysis.value.center[1] - center[1]) < 0.0001
  ) {
    handleClearAnalysis()
    return
  }

  clearSelectedEffects()
  if (!mapInstance || !amapApi || !isAmapReady.value) return

  activeLocationAnalysis.value = { name, center, isCurated: isCustomCommunity }
  const [centerLng, centerLat] = center

  // 1. 绘制梯度生活圈同心圆（由 customConfig.ts 统一管理半径、颜色与透明度）
  lifeCircleConfig.forEach((cfg) => {
    const circle = new amapApi.Circle({
      center: [centerLng, centerLat],
      radius: cfg.radius,
      strokeColor: cfg.strokeColor,
      strokeOpacity: cfg.strokeOpacity,
      strokeWeight: cfg.weight,
      strokeStyle: cfg.style,
      fillColor: cfg.fillColor,
      fillOpacity: cfg.fillOpacity,
      zIndex: 15,
      bubble: true,
    })

    // 标签位于圆圈顶部
    const tagLat = centerLat + cfg.radius / 111320
    const tagMarker = new amapApi.Marker({
      position: [centerLng, tagLat],
      content: `<div class="amap-circle-badge">${cfg.label}</div>`,
      offset: new amapApi.Pixel(-56, -12),
      zIndex: 20,
      clickable: false,
    })

    circleOverlays.push(circle, tagMarker)
  })
  mapInstance.add(circleOverlays)

  // 2. 绘制红线边界轮廓 (仅当高德返回真实 AOI 轮廓时绘制，绝不使用假矩形误导)
  const drawBoundary = (polygonPoints: Coordinate[]) => {
    if (!mapInstance || !isAmapReady.value) return
    const boundary = new amapApi.Polygon({
      path: polygonPoints,
      strokeColor: '#e56c55',
      strokeWeight: 2.5,
      strokeOpacity: 0.95,
      fillColor: '#e56c55',
      fillOpacity: 0.22,
      zIndex: 35,
      bubble: true,
    })
    boundaryOverlays.push(boundary)
    mapInstance.add(boundary)
  }

  if (placeSearchInstance && name && name !== '地图选定位置') {
    placeSearchInstance.search(name, (status: string, result: any) => {
      if (status === 'complete' && result?.poiList?.pois?.length) {
        const matchPoi = result.poiList.pois.find((p: any) => p.name.includes(name) || name.includes(p.name)) || result.poiList.pois[0]
        if (matchPoi?.aoi && typeof matchPoi.aoi === 'string') {
          const aoiPolygon = matchPoi.aoi.split(';').map((pt: string) => pt.split(',').map(Number) as Coordinate)
          if (aoiPolygon.length >= 3) {
            drawBoundary(aoiPolygon)
          }
        }
      }
    })
  }

  // 3. 点击底图点时展示信息窗体提示（方式3：点击窗体自带×关闭按钮即可清除生活圈）
  if (!isCustomCommunity) {
    if (!infoWindowInstance) {
      infoWindowInstance = new amapApi.InfoWindow({
        offset: new amapApi.Pixel(0, -20),
        isCustom: false,
      })
      infoWindowInstance.on('close', () => {
        if (!isProgrammaticClosing) {
          handleClearAnalysis()
        }
      })
    }
    infoWindowInstance.setContent(`
      <div class="amap-poi-infowindow">
        <div class="poi-infowindow-title">${name}</div>
        <div class="poi-infowindow-desc">📍 经纬度：${centerLng.toFixed(4)}, ${centerLat.toFixed(4)}</div>
        <div class="poi-infowindow-tags">
          <span class="tag-1km">🚶 1km 步行</span>
          <span class="tag-2km">🚲 2km 骑行</span>
          <span class="tag-3km">🚗 3km 驾车</span>
        </div>
      </div>
    `)
    isProgrammaticClosing = true
    infoWindowInstance.open(mapInstance, center)
    setTimeout(() => {
      isProgrammaticClosing = false
    }, 60)
  }
}

function renderSelectedEffects() {
  if (!props.selectedId) {
    clearSelectedEffects()
    return
  }
  const community = props.communities.find((item) => item.id === props.selectedId)
  if (community) {
    showLocationAnalysis(community.name, community.center, true)
  }
}

function renderAmap() {
  if (!mapInstance || !amapApi || !isAmapReady.value) return
  amapOverlays.forEach((overlay) => mapInstance.remove(overlay))
  amapOverlays = []

  if (props.layer === 'area') {
    props.areas.forEach((area) => {
      const polygon = new amapApi.Polygon({
        path: area.polygon,
        strokeColor: area.color,
        strokeWeight: 2,
        strokeOpacity: 0.85,
        fillColor: area.color,
        fillOpacity: 0.1,
      })
      const label = new amapApi.Marker({
        position: area.center,
        content: `<span class="amap-area-label" style="border-color:${area.color}">${area.name}</span>`,
        offset: new amapApi.Pixel(-34, -14),
      })
      polygon.on('click', () => emit('area-select', area.id))
      amapOverlays.push(polygon, label)
    })
  } else {
    props.communities.forEach((community) => {
      const name = props.showCommunityNames || community.id === props.selectedId ? `<strong>${community.name}</strong>` : ''
      const content = props.layer === 'price' && props.showPrices
        ? `<button class="amap-price-marker ${community.id === props.selectedId ? 'active-selected' : ''}">${name}<span>${community.listingCount}套</span><b>${formatWan(community.listingPrice)}</b></button>`
        : `<button class="amap-community-marker ${community.id === props.selectedId ? 'active-selected' : ''}">${name || '小区'}</button>`
      const marker = new amapApi.Marker({
        position: community.center,
        content,
        offset: new amapApi.Pixel(-30, -18),
        zIndex: community.id === props.selectedId ? 100 : 10,
      })
      marker.on('click', () => emit('select', community.id))
      amapOverlays.push(marker)
    })
  }

  if (props.showPois && props.layer !== 'area') {
    props.pois.forEach((poi) => {
      amapOverlays.push(
        new amapApi.Marker({
          position: poi.center,
          content: `<span class="amap-poi-marker">${poiBadge(poi.category)} ${poi.name}</span>`,
          offset: new amapApi.Pixel(-22, -14),
          zIndex: 8,
        }),
      )
    })
  }

  if (props.drawMode && props.drawPoints.length >= 2) {
    amapOverlays.push(
      new amapApi.Polyline({
        path: props.drawPoints,
        strokeColor: '#2f6df6',
        strokeWeight: 3,
        strokeStyle: 'dashed',
        strokeOpacity: 0.9,
      }),
    )
  }

  mapInstance.add(amapOverlays)
}

watch(
  () => [
    props.layer,
    props.showPois,
    props.showPrices,
    props.showCommunityNames,
    props.communities,
    props.areas,
    props.pois,
    props.drawMode,
    props.drawPoints,
  ],
  renderAmap,
  { deep: true },
)

watch(() => props.baseMapType, updateBaseMap)
watch(() => props.selectedId, renderSelectedEffects)
watch(() => [props.enableViewportScan, props.showCommunityNames], () => {
  if (props.enableViewportScan) {
    scanViewportCommunities()
  } else {
    clearDiscoveredMarkers()
  }
})

onMounted(loadAmap)

onBeforeUnmount(() => {
  clearSelectedEffects()
  clearDiscoveredMarkers()
  clearTimeout(scanDebounceTimer)
  if (mapInstance) {
    mapInstance.destroy()
    mapInstance = null
  }
})

defineExpose({
  focusCommunity(id: string) {
    const community = props.communities.find((item) => item.id === id)
    if (community && mapInstance) {
      mapInstance.setZoomAndCenter(15, community.center)
    }
  },
})
</script>


