<template>
  <aside v-if="community" class="detail-drawer">
    <div class="detail-header">
      <div>
        <div class="detail-kicker">小区档案 · {{ community.plate }}</div>
        <h2>{{ community.name }}</h2>
        <p>{{ community.developer }} · {{ community.buildYear }} 年建 · {{ community.propertyCompany }}</p>
      </div>
      <div class="detail-actions">
        <button class="icon-button" :class="{ active: community.favorite }" type="button" :title="community.favorite ? '取消收藏' : '收藏小区'" @click="$emit('toggle-favorite')">
          <Heart :size="18" :fill="community.favorite ? 'currentColor' : 'none'" />
        </button>
        <button class="icon-button" type="button" title="关闭详情" @click="$emit('close')"><X :size="18" /></button>
      </div>
    </div>

    <div class="detail-stats">
      <div class="detail-stat primary">
        <span>挂牌均价</span>
        <strong>{{ formatPrice(community.listingPrice) }}</strong>
        <small>最新快照 · {{ community.lastUpdated }}</small>
      </div>
      <div class="detail-stat">
        <span>成交参考</span>
        <strong>{{ formatPrice(community.transactionPrice) }}</strong>
        <small>独立口径</small>
      </div>
      <div class="detail-stat">
        <span>在售房源</span>
        <strong>{{ community.listingCount }}<em> 套</em></strong>
        <small>公开样本量</small>
      </div>
    </div>

    <section class="detail-section trend-section">
      <div class="section-heading">
        <div>
          <span class="section-eyebrow">PRICE TREND</span>
          <h3>价格走势</h3>
        </div>
        <div class="metric-switcher" role="tablist" aria-label="价格口径">
          <button :class="{ active: metric === 'listing' }" type="button" @click="metric = 'listing'">挂牌</button>
          <button :class="{ active: metric === 'transaction' }" type="button" @click="metric = 'transaction'">成交</button>
        </div>
      </div>
      <div ref="chartElement" class="price-chart"></div>
      <div class="chart-footnote"><span class="chart-line"></span>数据点为历史快照，缺失月份不会插值</div>
    </section>

    <section class="detail-section">
      <div class="section-heading compact-heading">
        <div>
          <span class="section-eyebrow">PERSONAL NOTES</span>
          <h3>我的判断</h3>
        </div>
        <button class="text-button" type="button" @click="$emit('save-note', noteDraft)">保存笔记</button>
      </div>
      <textarea v-model="noteDraft" class="note-input" placeholder="记录看房时的优缺点、噪音、物业和通勤感受"></textarea>
    </section>

    <section class="detail-section">
      <div class="section-heading compact-heading">
        <div>
          <span class="section-eyebrow">TAGS</span>
          <h3>个人标签</h3>
        </div>
      </div>
      <div class="tag-list">
        <span v-for="tag in community.tags" :key="tag" class="tag-chip">{{ tag }}</span>
        <form class="tag-add" @submit.prevent="addTag">
          <input v-model="tagDraft" aria-label="新增标签" placeholder="新增标签" />
          <button type="submit" title="添加标签"><Plus :size="14" /></button>
        </form>
      </div>
    </section>

    <section class="source-strip">
      <div class="source-icon"><Database :size="16" /></div>
      <div>
        <strong>{{ community.source }}</strong>
        <span>最后更新 {{ community.lastUpdated }} · 仅作看房参考</span>
      </div>
      <button class="refresh-button" type="button" title="手动刷新数据" @click="$emit('refresh')"><RefreshCw :size="15" /></button>
    </section>
    <div v-if="refreshMessage" class="refresh-message"><Info :size="15" />{{ refreshMessage }}</div>
  </aside>
</template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { Database, Heart, Info, Plus, RefreshCw, X } from 'lucide-vue-next'
import type { Community, PriceMetric } from '../types'

const props = defineProps<{ community?: Community; refreshMessage?: string }>()
const emit = defineEmits<{
  (event: 'close'): void
  (event: 'toggle-favorite'): void
  (event: 'save-note', note: string): void
  (event: 'add-tag', tag: string): void
  (event: 'refresh'): void
}>()

const chartElement = ref<HTMLElement | null>(null)
const metric = ref<PriceMetric>('listing')
const noteDraft = ref('')
const tagDraft = ref('')
let chart: echarts.ECharts | null = null
let mounted = false
const handleResize = () => chart?.resize()

function formatPrice(value: number) {
  return `${(value / 10000).toFixed(2)}万/㎡`
}

function addTag() {
  const tag = tagDraft.value.trim()
  if (!tag || !props.community || props.community.tags.includes(tag)) return
  emit('add-tag', tag)
  tagDraft.value = ''
}

function drawChart() {
  if (!mounted || !chartElement.value || !props.community) return
  if (!chart) chart = echarts.init(chartElement.value)
  const points = props.community.snapshots
    .filter((snapshot) => snapshot.metric === metric.value)
    .sort((a, b) => a.capturedAt.localeCompare(b.capturedAt))
  chart.setOption({
    animation: false,
    grid: { left: 8, right: 10, top: 22, bottom: 18, containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: points.map((point) => point.capturedAt.slice(0, 7)),
      axisLine: { lineStyle: { color: '#dfe5ed' } },
      axisTick: { show: false },
      axisLabel: { color: '#8792a2', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      scale: true,
      splitNumber: 3,
      axisLabel: { color: '#8792a2', fontSize: 10, formatter: (value: number) => `${(value / 10000).toFixed(1)}万` },
      splitLine: { lineStyle: { color: '#edf0f4', type: 'dashed' } },
    },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value: number) => `${value.toLocaleString()} 元/㎡`,
      backgroundColor: '#172230',
      borderWidth: 0,
      textStyle: { color: '#fff', fontSize: 12 },
    },
    series: [{
      type: 'line',
      data: points.map((point) => point.value),
      smooth: 0.25,
      showSymbol: true,
      symbolSize: 7,
      itemStyle: { color: '#2f6df6', borderColor: '#fff', borderWidth: 2 },
      lineStyle: { color: '#2f6df6', width: 2.5 },
      areaStyle: { color: 'rgba(47, 109, 246, 0.08)' },
    }],
  })
}

watch(() => [props.community, metric.value], async () => {
  noteDraft.value = props.community?.note ?? ''
  await nextTick()
  drawChart()
}, { deep: true })

onMounted(async () => {
  mounted = true
  noteDraft.value = props.community?.note ?? ''
  await nextTick()
  drawChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  mounted = false
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>
