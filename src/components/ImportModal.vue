<template>
  <div v-if="open" class="modal-backdrop" @click.self="$emit('close')">
    <section class="import-modal" role="dialog" aria-modal="true" aria-labelledby="import-title">
      <div class="modal-header">
        <div>
          <span class="section-eyebrow">DATA IMPORT</span>
          <h2 id="import-title">更新房产数据</h2>
          <p>导入后会保留历史快照，不会覆盖已有价格趋势。</p>
        </div>
        <button class="icon-button" type="button" title="关闭" @click="$emit('close')"><X :size="18" /></button>
      </div>
      <label class="file-dropzone" :class="{ selected: fileName }">
        <input type="file" accept=".json,.csv,application/json,text/csv" @change="handleFile" />
        <UploadCloud :size="24" />
        <strong>{{ fileName || '选择 JSON 或 CSV 文件' }}</strong>
        <span>{{ fileName ? `${previewCommunities.length} 条小区记录待导入` : '支持小区基础信息和价格快照' }}</span>
      </label>
      <div v-if="errorMessage" class="form-error"><AlertTriangle :size="16" />{{ errorMessage }}</div>
      <div v-if="previewCommunities.length" class="import-preview">
        <div class="preview-heading"><span>导入预览</span><strong>{{ previewCommunities.length }} 个小区</strong></div>
        <div class="preview-list">
          <div v-for="community in previewCommunities.slice(0, 4)" :key="community.id" class="preview-row">
            <span>{{ community.name }}</span><span>{{ community.plate }}</span><strong>{{ formatWan(community.listingPrice) }}</strong>
          </div>
        </div>
        <small v-if="previewCommunities.length > 4">还有 {{ previewCommunities.length - 4 }} 条记录</small>
      </div>
      <div class="modal-footer">
        <button class="button secondary" type="button" @click="$emit('close')">取消</button>
        <button class="button primary" type="button" :disabled="!previewCommunities.length" @click="submitImport"><Upload :size="16" />导入数据</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { AlertTriangle, Upload, UploadCloud, X } from 'lucide-vue-next'
import type { Community } from '../types'

defineProps<{ open: boolean }>()
const emit = defineEmits<{
  (event: 'close'): void
  (event: 'import', communities: Community[]): void
}>()

const fileName = ref('')
const previewCommunities = ref<Community[]>([])
const errorMessage = ref('')

function formatWan(value: number) {
  return `${(value / 10000).toFixed(2)}万`
}

function normalizeCommunity(item: any, index: number): Community {
  const center = Array.isArray(item.center) ? item.center : [Number(item.lng) || 119.38, Number(item.lat) || 25.72]
  const listingPrice = Number(item.listingPrice ?? item.current_price ?? item.price ?? 0)
  const transactionPrice = Number(item.transactionPrice ?? item.dealPrice ?? listingPrice)
  return {
    id: String(item.id ?? item.community_id ?? `import-${Date.now()}-${index}`),
    name: String(item.name ?? item.communityName ?? '未命名小区'),
    plate: String(item.plate ?? item.district ?? '未分片区'),
    center: [Number(center[0]), Number(center[1])],
    listingPrice,
    transactionPrice,
    listingCount: Number(item.listingCount ?? item.listings ?? 0),
    buildYear: Number(item.buildYear ?? item.year ?? 0),
    developer: String(item.developer ?? '未记录'),
    propertyCompany: String(item.propertyCompany ?? item.property ?? '未记录'),
    tags: Array.isArray(item.tags) ? item.tags.map(String) : [],
    lastUpdated: String(item.lastUpdated ?? new Date().toISOString().slice(0, 10)),
    source: String(item.source ?? '手动导入'),
    note: String(item.note ?? item.user_notes ?? ''),
    favorite: Boolean(item.favorite),
    snapshots: Array.isArray(item.snapshots) ? item.snapshots : [{ metric: 'listing', value: listingPrice, capturedAt: String(item.lastUpdated ?? new Date().toISOString().slice(0, 10)) }],
  }
}

function parseCsv(text: string) {
  const [headerLine, ...lines] = text.split(/\r?\n/).filter(Boolean)
  const headers = headerLine.split(',').map((header) => header.trim())
  return lines.map((line) => {
    const values = line.split(',').map((value) => value.trim())
    return Object.fromEntries(headers.map((header, index) => [header, values[index]]))
  })
}

async function handleFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  fileName.value = file.name
  errorMessage.value = ''
  try {
    const text = await file.text()
    const raw = file.name.toLowerCase().endsWith('.csv') ? parseCsv(text) : JSON.parse(text)
    const items = Array.isArray(raw) ? raw : raw.communities
    if (!Array.isArray(items)) throw new Error('文件中没有 communities 数组')
    previewCommunities.value = items.map(normalizeCommunity)
  } catch (error) {
    previewCommunities.value = []
    errorMessage.value = error instanceof Error ? error.message : '文件解析失败'
  }
}

function submitImport() {
  emit('import', previewCommunities.value)
  fileName.value = ''
  previewCommunities.value = []
}
</script>
