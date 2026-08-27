/**
 * ====================================================================
 *                福清找房地图 - 自定义配置中心 (Custom Config)
 * ====================================================================
 * 说明：
 * 本文件统一管理全系统的颜色、尺寸、透明度、图层样式、生活圈半径、
 * 以及高德动态扫描等所有核心视觉与业务参数。
 * 后续有任何样式、尺寸、色彩或参数调整，直接在此处修改即可全局生效。
 */

export interface LifeCircleItemConfig {
  radius: number          // 半径（米）
  label: string           // 标签文案
  fillColor: string       // 填充颜色
  fillOpacity: number     // 填充透明度 (0 ~ 1)
  strokeColor: string     // 边框颜色
  strokeOpacity: number   // 边框透明度 (0 ~ 1)
  weight: number          // 边框粗细 (px)
  style: 'solid' | 'dashed' // 边框样式：实线 / 虚线
}

/**
 * 1. 地图与区域遮罩配置 (Map & District Mask Config)
 */
export const mapThemeConfig = {
  // 是否启用福清市行政区划反向遮罩（true: 仅展示福清市内地图；false: 全域正常展示高德底图）
  enableDistrictMask: false,
  // 福清市行政边界发光轮廓颜色
  districtBorderColor: '#2f6df6',
  // 福清市行政边界轮廓粗细
  districtBorderWeight: 2.2,
  // 福清市行政边界轮廓透明度
  districtBorderOpacity: 0.9,
  // 福清市外部遮蔽底色（反向镂空区域背景色）
  maskFillColor: '#dfe5ec',
  // 福清市外部遮蔽底色透明度
  maskFillOpacity: 0.96,
}

/**
 * 2. 小区标注气泡尺寸与颜色配置 (Community Marker & Badge Config)
 */
export const markerThemeConfig = {
  // --- 已整理/重点关注小区 (Local Curated Communities) ---
  curatedCommunity: {
    bgColor: '#2f6df6',          // 气泡主背景色（科技蓝）
    textColor: '#ffffff',        // 文本颜色
    pricePillBg: '#ffffff',      // 价格胶囊背景色
    pricePillColor: '#2f6df6',   // 价格胶囊字体色
    selectedBorderColor: '#ff4d4f', // 选中时的高亮外圈边框色（珊瑚红）
    selectedShadow: '0 0 0 3px #ff4d4f, 0 8px 24px rgba(255, 77, 79, 0.35)',
    fontSize: '11px',            // 字体大小
    borderRadius: '16px',        // 圆角大小
    padding: '6px 9px',          // 内边距
  },

  // --- 高德全城实时动态扫描发现的小区 (GaoDe Discovered Communities) ---
  discoveredCommunity: {
    bgColor: '#0f766e',          // 气泡主背景色（松石墨绿，与重点小区明显区隔）
    textColor: '#ffffff',        // 文本颜色
    hoverBorderColor: '#14b8a6', // 鼠标悬浮边框色
    selectedBorderColor: '#ff4d4f', // 选中边框色
    iconColor: '#2dd4bf',        // 图标高亮色
    fontSize: '10.5px',          // 字体大小
    borderRadius: '13px',        // 圆角大小
    padding: '4px 8px',          // 内边距
  },
}

/**
 * 3. 梯度生活圈同心圆配置 (1km / 2km / 3km Life Circles Config)
 */
export const lifeCircleConfig: LifeCircleItemConfig[] = [
  {
    radius: 1000,
    label: '🚶 1km 步行生活圈',
    fillColor: '#2f6df6',
    fillOpacity: 0.15,
    strokeColor: '#2f6df6',
    strokeOpacity: 0.85,
    weight: 1.5,
    style: 'solid',
  },
  {
    radius: 2000,
    label: '🚲 2km 骑行生活圈',
    fillColor: '#18a48c',
    fillOpacity: 0.08,
    strokeColor: '#18a48c',
    strokeOpacity: 0.6,
    weight: 1.2,
    style: 'dashed',
  },
  {
    radius: 3000,
    label: '🚗 3km 驾车生活圈',
    fillColor: '#df8a35',
    fillOpacity: 0.035,
    strokeColor: '#df8a35',
    strokeOpacity: 0.45,
    weight: 1,
    style: 'dashed',
  },
]

/**
 * 4. POI 行业分类图标与标签色彩 (POI Categories Config)
 */
export const poiCategoryColors: Record<string, { bg: string; text: string; badge: string }> = {
  hospital: { bg: '#edf9f8', text: '#25a6b3', badge: '医' },
  school: { bg: '#f5f0ff', text: '#8064d8', badge: '学' },
  mall: { bg: '#fff2f0', text: '#e56c55', badge: '商' },
  transit: { bg: '#eef4ff', text: '#2f6df6', badge: '站' },
  park: { bg: '#edf8f2', text: '#2d9d70', badge: '园' },
}

/**
 * 5. 高德全城小区按视野动态扫描配置 (Viewport PlaceSearch Config)
 */
export const viewportScanConfig = {
  // 是否默认开启当前视野小区动态扫描（当前为默认关闭）
  defaultEnabled: false,
  // 触发扫描的最小缩放级别（推荐 >= 13，放大到街区级才开始高密度扫描，防止全国视野浪费请求）
  minZoom: 13,
  // 视野移动或缩放停止后的防抖延时（毫秒）
  debounceMs: 350,
  // 每次范围检索单页返回的最大小区数量 (1 ~ 50)
  pageSize: 40,
  // 高德 POI 住宅小区分类代码及关键词
  types: '120300|120301|120302|商务住宅|住宅区|住宅小区',
}

/**
 * 6. 图层分级缩放阈值配置 (Layer Zoom Level Config)
 */
export const layerZoomConfig = {
  // 小于该缩放等级展示「片区概览」(Area Layer，默认为小于 14 级展示)
  areaMaxZoom: 14,
  // 小于该缩放等级展示「小区分布」(Community Layer)，大于等于该级别展示「价格标签」(Price Layer)
  communityMaxZoom: 15.5,
}

