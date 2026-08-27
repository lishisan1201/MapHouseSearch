<template>
  <main class="app-shell">
    <MapCanvas
      ref="mapRef"
      :areas="areas"
      :communities="filteredCommunities"
      :zoom="zoom"
      :selected-id="selectedId"
      :layer="visibleLayer"
      :base-map-type="baseMapType"
      :enable-viewport-scan="enableViewportScan"
      :show-community-names="showCommunityNames"
      :show-prices="showPrices"
      :draw-mode="drawMode"
      :draw-points="drawPoints"
      @select="selectCommunity"
      @area-select="selectArea"
      @zoom-change="zoom = $event"
      @draw-point="drawPoints.push($event)"
      @discovered-scan="discoveredCount = $event"
    />

    <header class="topbar">
      <div class="brand-block">
        <div class="brand-mark"><MapPinned :size="21" /></div>
        <div>
          <strong>福清找房地图</strong>
          <span>个人房产工作台</span>
        </div>
      </div>

      <div class="search-area">
        <div class="search-box" :class="{ focused: searchInput }">
          <Search :size="19" />
          <input v-model="searchInput" type="search" placeholder="搜索小区或片区" @keydown.esc="searchInput = ''" />
          <button v-if="searchInput" class="clear-search" type="button" title="清空搜索" @click="searchInput = ''"><X :size="15" /></button>
        </div>
        <div v-if="searchInput && searchResults.length" class="search-results">
          <button v-for="community in searchResults.slice(0, 5)" :key="community.id" type="button" @click="selectCommunity(community.id)">
            <span class="result-pin"><Home :size="14" /></span>
            <span><strong>{{ community.name }}</strong><small>{{ community.plate }} · {{ formatPrice(community.listingPrice) }}</small></span>
            <ArrowUpRight :size="15" />
          </button>
        </div>
      </div>

      <div class="top-actions">
        <div class="control-wrap">
          <button class="toolbar-button" type="button" :class="{ active: baseMapMenuOpen }" @click="baseMapMenuOpen = !baseMapMenuOpen">
            <Globe :size="16" />{{ baseMapLabels[baseMapType] }}<ChevronDown :size="14" />
          </button>
          <div v-if="baseMapMenuOpen" class="popover basemap-popover">
            <div class="popover-title">底图模式 <button type="button" title="关闭底图选择" @click="baseMapMenuOpen = false"><X :size="15" /></button></div>
            <div class="basemap-options">
              <button
                v-for="opt in baseMapOptions"
                :key="opt.value"
                type="button"
                class="basemap-option-card"
                :class="{ active: baseMapType === opt.value }"
                @click="baseMapType = opt.value; baseMapMenuOpen = false"
              >
                <div class="opt-icon"><component :is="opt.icon" :size="16" /></div>
                <div class="opt-info">
                  <strong>{{ opt.title }}</strong>
                  <small>{{ opt.desc }}</small>
                </div>
              </button>
            </div>
          </div>
        </div>

        <div class="control-wrap">
          <button class="toolbar-button" type="button" :class="{ active: filterMenuOpen }" @click="filterMenuOpen = !filterMenuOpen"><SlidersHorizontal :size="16" />筛选<span v-if="activeFilterCount" class="filter-count">{{ activeFilterCount }}</span><ChevronDown :size="14" /></button>
          <div v-if="filterMenuOpen" class="popover filter-popover">
            <div class="popover-title">筛选小区 <button type="button" title="关闭筛选" @click="filterMenuOpen = false"><X :size="15" /></button></div>
            <label>片区<select v-model="selectedPlate"><option value="">全部片区</option><option v-for="plate in plates" :key="plate" :value="plate">{{ plate }}</option></select></label>
            <label>标签<select v-model="selectedTag"><option value="">全部标签</option><option v-for="tag in tags" :key="tag" :value="tag">{{ tag }}</option></select></label>
            <label>挂牌均价<input v-model.number="minPrice" type="number" min="0" step="500" placeholder="最低元/㎡" /></label>
            <label>至<input v-model.number="maxPrice" type="number" min="0" step="500" placeholder="最高元/㎡" /></label>
            <button class="reset-filter" type="button" @click="resetFilters">重置筛选</button>
          </div>
        </div>
        <div class="control-wrap">
          <button class="toolbar-button" type="button" :class="{ active: layerMenuOpen }" @click="layerMenuOpen = !layerMenuOpen"><Layers3 :size="16" />图层<ChevronDown :size="14" /></button>
          <div v-if="layerMenuOpen" class="popover layer-popover">
            <div class="popover-title">地图图层 <button type="button" title="关闭图层" @click="layerMenuOpen = false"><X :size="15" /></button></div>
            <label class="toggle-row"><span><MapPin :size="16" />已整理小区</span><input v-model="showCommunityNames" type="checkbox" /><i></i></label>
            <label class="toggle-row"><span><Radar :size="16" />高德全城小区扫描 <small v-if="discoveredCount" class="badge-count">{{ discoveredCount }}</small></span><input v-model="enableViewportScan" type="checkbox" /><i></i></label>
            <label class="toggle-row"><span><Tag :size="16" />价格气泡</span><input v-model="showPrices" type="checkbox" /><i></i></label>
          </div>
        </div>
        <button class="toolbar-button import-action" type="button" @click="importOpen = true"><Upload :size="16" />导入数据</button>
        <button class="icon-button draw-action" :class="{ active: drawMode }" type="button" title="在地图上绘制片区" @click="toggleDrawMode"><PencilRuler :size="18" /></button>
      </div>
    </header>

    <section class="result-panel">
      <div class="result-panel-head">
        <div>
          <span class="eyebrow">VISIBLE AREA</span>
          <h1>主城区找房</h1>
        </div>
        <button class="icon-button subtle" type="button" title="收起列表" @click="resultPanelCollapsed = !resultPanelCollapsed"><ChevronUp v-if="!resultPanelCollapsed" :size="18" /><ChevronDown v-else :size="18" /></button>
      </div>
      <div v-if="!resultPanelCollapsed" class="result-panel-body">
        <div class="result-count">
          <strong>{{ filteredCommunities.length }}</strong><span>个已整理小区</span>
          <span class="count-divider">·</span><span>平均 {{ formatPrice(averagePrice) }}</span>
          <span v-if="enableViewportScan && discoveredCount" class="discovered-tag">已扫描 {{ discoveredCount }} 个小区</span>
        </div>
        <div class="result-list">
          <button v-for="community in sortedCommunities.slice(0, 7)" :key="community.id" class="result-card" :class="{ selected: selectedId === community.id }" type="button" @click="selectCommunity(community.id)">
            <span class="result-card-main"><strong>{{ community.name }}</strong><small>{{ community.plate }}</small></span>
            <span class="result-card-price"><strong>{{ formatPrice(community.listingPrice) }}</strong><small>{{ community.listingCount }} 套</small></span>
          </button>
        </div>
        <div v-if="filteredCommunities.length > 7" class="list-more">地图上展示全部 {{ filteredCommunities.length }} 个结果</div>
      </div>
    </section>

    <div class="map-toolbar">
      <div class="layer-state"><span class="layer-dot" :class="visibleLayer"></span><strong>{{ layerLabel }}</strong><span>·</span><span>{{ zoom.toFixed(1) }} 级</span></div>
      <div class="zoom-controls">
        <button type="button" title="放大地图" @click="zoom = Math.min(18, zoom + 0.5)"><Plus :size="17" /></button>
        <button type="button" title="缩小地图" @click="zoom = Math.max(11, zoom - 0.5)"><Minus :size="17" /></button>
      </div>
    </div>

    <div v-if="drawMode" class="draw-toolbar">
      <div><PencilRuler :size="17" /><strong>正在绘制自定义片区</strong><span>{{ drawPoints.length }} 个边界点</span></div>
      <button class="button primary small" type="button" :disabled="drawPoints.length < 3" @click="openAreaEditor">完成并保存</button>
      <button class="button ghost small" type="button" @click="cancelDrawing">取消</button>
    </div>

    <div v-if="toastMessage" class="toast-message"><CheckCircle2 :size="16" />{{ toastMessage }}</div>

    <CommunityDetail
      v-if="selectedCommunity"
      :community="selectedCommunity"
      :refresh-message="refreshMessage"
      @close="selectedId = undefined"
      @toggle-favorite="toggleFavorite"
      @save-note="saveNote"
      @add-tag="addTag"
      @refresh="refreshCommunity"
    />

    <ImportModal :open="importOpen" @close="importOpen = false" @import="importCommunities" />

    <div v-if="areaEditorOpen" class="modal-backdrop" @click.self="areaEditorOpen = false">
      <section class="area-editor" role="dialog" aria-modal="true" aria-labelledby="area-title">
        <div class="modal-header"><div><span class="section-eyebrow">CUSTOM AREA</span><h2 id="area-title">保存片区</h2><p>为刚才绘制的边界添加名称和颜色。</p></div><button class="icon-button" type="button" title="关闭" @click="areaEditorOpen = false"><X :size="18" /></button></div>
        <label>片区名称<input v-model="newAreaName" autofocus placeholder="例如：福清西站片区" @keydown.enter="saveArea" /></label>
        <label>边界颜色<div class="color-options"><button v-for="color in areaColors" :key="color" class="color-swatch" :class="{ active: newAreaColor === color }" :style="{ backgroundColor: color }" type="button" :title="`选择${color}`" @click="newAreaColor = color"></button></div></label>
        <div class="modal-footer"><button class="button secondary" type="button" @click="areaEditorOpen = false">取消</button><button class="button primary" type="button" :disabled="!newAreaName.trim()" @click="saveArea"><Save :size="16" />保存片区</button></div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ArrowUpRight, Box, CheckCircle2, ChevronDown, ChevronUp, Globe, Home, Layers3, MapPin, MapPinned, Minus, PencilRuler, Plus, Radar, Save, Search, SlidersHorizontal, Tag, Upload, X } from 'lucide-vue-next'
import MapCanvas from './components/MapCanvas.vue'
import CommunityDetail from './components/CommunityDetail.vue'
import ImportModal from './components/ImportModal.vue'
import { demoData } from './data/demoData'
import { createArea as apiCreateArea, importCommunities as apiImportCommunities, loadMapData, refreshCommunity as apiRefreshCommunity, updatePersonal } from './lib/api'
import { filterCommunities, getVisibleLayer, searchCommunities } from './lib/mapUtils'
import type { Area, BaseMapType, Community, Coordinate, MapLayer } from './types'
import { viewportScanConfig } from './customConfig'

const areas = ref<Area[]>(demoData.areas.map((area) => ({ ...area, polygon: area.polygon.map((point) => [...point] as Coordinate) })))
const communities = ref<Community[]>(demoData.communities.map((community) => ({ ...community, tags: [...community.tags], snapshots: community.snapshots.map((snapshot) => ({ ...snapshot })) })))
const zoom = ref(13.5)
const selectedId = ref<string>()
const baseMapType = ref<BaseMapType>('normal')
const baseMapMenuOpen = ref(false)
const enableViewportScan = ref(viewportScanConfig.defaultEnabled)
const discoveredCount = ref(0)
const baseMapLabels: Record<BaseMapType, string> = {
  normal: '标准全彩',
  '3d': '3D立体',
  satellite: '卫星影像',
}
const baseMapOptions = [
  { value: 'normal' as BaseMapType, title: '标准全彩', desc: '学校/商圈/路网要素鲜明', icon: MapPin },
  { value: '3d' as BaseMapType, title: '3D立体', desc: '52°立体倾角与建筑模型', icon: Box },
  { value: 'satellite' as BaseMapType, title: '卫星影像', desc: '高清航拍影像与路网叠加', icon: Globe },
]
const searchInput = ref('')
const selectedPlate = ref('')
const selectedTag = ref('')
const minPrice = ref<number>()
const maxPrice = ref<number>()
const showCommunityNames = ref(true)
const showPrices = ref(true)
const filterMenuOpen = ref(false)
const layerMenuOpen = ref(false)
const importOpen = ref(false)
const resultPanelCollapsed = ref(false)
const drawMode = ref(false)
const drawPoints = ref<Coordinate[]>([])
const areaEditorOpen = ref(false)
const newAreaName = ref('')
const newAreaColor = ref('#2f6df6')
const toastMessage = ref('')
const refreshMessage = ref('')
const noteDrafts = ref<Record<string, string>>({})
const mapRef = ref<InstanceType<typeof MapCanvas> | null>(null)
let toastTimer: number | undefined

const areaColors = ['#2f6df6', '#18a48c', '#df8a35', '#d95c67', '#8564d8']
const plates = computed(() => Array.from(new Set(communities.value.map((community) => community.plate))))
const tags = computed(() => Array.from(new Set(communities.value.flatMap((community) => community.tags))))
const searchResults = computed(() => searchCommunities(communities.value, searchInput.value))
const filteredCommunities = computed(() => filterCommunities(searchResults.value, { plate: selectedPlate.value || undefined, tag: selectedTag.value || undefined, minPrice: minPrice.value, maxPrice: maxPrice.value }))
const sortedCommunities = computed(() => [...filteredCommunities.value].sort((a, b) => b.listingCount - a.listingCount))
const selectedCommunity = computed(() => communities.value.find((community) => community.id === selectedId.value))
const visibleLayer = computed<MapLayer>(() => getVisibleLayer(zoom.value))
const layerLabel = computed(() => ({ area: '片区概览', community: '小区分布', price: '价格标签' })[visibleLayer.value])
const averagePrice = computed(() => filteredCommunities.value.length ? Math.round(filteredCommunities.value.reduce((sum, community) => sum + community.listingPrice, 0) / filteredCommunities.value.length) : 0)
const activeFilterCount = computed(() => [selectedPlate.value, selectedTag.value, minPrice.value, maxPrice.value].filter(Boolean).length)

function formatPrice(value: number) {
  return value ? `${(value / 10000).toFixed(2)}万` : '暂无'
}

function selectCommunity(id: string) {
  selectedId.value = id
  refreshMessage.value = ''
  mapRef.value?.focusCommunity(id)
}

function selectArea(id: string) {
  const area = areas.value.find((item) => item.id === id)
  if (area) showToast(`已选中片区：${area.name}`)
}

function resetFilters() {
  selectedPlate.value = ''
  selectedTag.value = ''
  minPrice.value = undefined
  maxPrice.value = undefined
}

function toggleFavorite() {
  if (!selectedCommunity.value) return
  selectedCommunity.value.favorite = !selectedCommunity.value.favorite
  void updatePersonal(selectedCommunity.value.id, { favorite: selectedCommunity.value.favorite }).catch(() => undefined)
  persistState()
}

function saveNote(note: string) {
  if (!selectedCommunity.value) return
  selectedCommunity.value.note = note
  noteDrafts.value[selectedCommunity.value.id] = note
  void updatePersonal(selectedCommunity.value.id, { note }).catch(() => undefined)
  persistState()
  showToast('笔记已保存')
}

function addTag(tag: string) {
  if (!selectedCommunity.value || selectedCommunity.value.tags.includes(tag)) return
  selectedCommunity.value.tags.push(tag)
  void updatePersonal(selectedCommunity.value.id, { tags: selectedCommunity.value.tags }).catch(() => undefined)
  persistState()
  showToast(`已添加标签：${tag}`)
}

function refreshCommunity() {
  if (!selectedCommunity.value) return
  refreshMessage.value = '当前未配置自动采集源，请导入最新 JSON / CSV 数据更新。'
  void apiRefreshCommunity(selectedCommunity.value.id).then((result) => { refreshMessage.value = result.message }).catch(() => undefined)
}

function toggleDrawMode() {
  drawMode.value = !drawMode.value
  drawPoints.value = []
  areaEditorOpen.value = false
}

function cancelDrawing() {
  drawMode.value = false
  drawPoints.value = []
}

function openAreaEditor() {
  if (drawPoints.value.length >= 3) areaEditorOpen.value = true
}

function saveArea() {
  if (!newAreaName.value.trim() || drawPoints.value.length < 3) return
  const center = drawPoints.value.reduce((sum, point) => [sum[0] + point[0], sum[1] + point[1]], [0, 0]).map((value) => value / drawPoints.value.length) as Coordinate
  const newArea: Area = { id: `custom-${Date.now()}`, name: newAreaName.value.trim(), type: 'custom', color: newAreaColor.value, minZoom: 10, maxZoom: 12.5, center, polygon: [...drawPoints.value] }
  areas.value.push(newArea)
  void apiCreateArea(newArea).catch(() => undefined)
  areaEditorOpen.value = false
  drawMode.value = false
  drawPoints.value = []
  newAreaName.value = ''
  persistState()
  showToast('自定义片区已保存')
}

function importCommunities(imported: Community[]) {
  imported.forEach((incoming) => {
    const existingIndex = communities.value.findIndex((community) => community.id === incoming.id || community.name === incoming.name)
    if (existingIndex >= 0) communities.value[existingIndex] = { ...communities.value[existingIndex], ...incoming, tags: incoming.tags.length ? incoming.tags : communities.value[existingIndex].tags }
    else communities.value.push(incoming)
  })
  importOpen.value = false
  void apiImportCommunities(imported).catch(() => undefined)
  persistState()
  showToast(`已导入 ${imported.length} 个小区，历史快照已保留`)
}

function showToast(message: string) {
  toastMessage.value = message
  if (toastTimer) window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => { toastMessage.value = '' }, 2800)
}

function persistState() {
  localStorage.setItem('fuqing-house-map-state', JSON.stringify({ areas: areas.value, communities: communities.value }))
}

onMounted(() => {
  const saved = localStorage.getItem('fuqing-house-map-state')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed.areas)) areas.value = parsed.areas
      if (Array.isArray(parsed.communities)) communities.value = parsed.communities
      return
    } catch { localStorage.removeItem('fuqing-house-map-state') }
  }
  void loadMapData().then((remote) => {
    if (remote.communities?.length) communities.value = remote.communities
    if (remote.areas?.length) areas.value = remote.areas
    if (remote.pois?.length) pois.value = remote.pois
  }).catch(() => undefined)
})

watch(() => selectedCommunity.value?.id, (id) => {
  if (id && selectedCommunity.value) noteDrafts.value[id] = selectedCommunity.value.note
})

watch(() => selectedCommunity.value?.note, (note) => {
  if (selectedId.value && note !== undefined) noteDrafts.value[selectedId.value] = note
})

watch(() => searchInput.value, () => {
  if (!searchInput.value) selectedId.value = undefined
})

</script>
