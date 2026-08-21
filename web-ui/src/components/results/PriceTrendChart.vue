<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface TrendPoint {
  day: string
  avg_price: number | null
  median_price: number | null
  min_price?: number | null
}

const props = defineProps<{
  points: TrendPoint[]
}>()
const { t } = useI18n()

const chartWidth = 720
const chartHeight = 240
// 水平留白仅用于曲线横向定位；纵向另外拆分出顶部/底部的专用留白，
// 避免最高价/最低价标记的文字跟坐标轴日期、网格线挤在一起。
const paddingX = 24
const plotTop = 34
const axisLabelHeight = 20
const extremeLabelGap = 30
const plotBottom = chartHeight - axisLabelHeight - extremeLabelGap

const validPoints = computed(() =>
  props.points.filter((point) => point.avg_price !== null && point.avg_price !== undefined)
)

const valueRange = computed(() => {
  const values = validPoints.value
    .flatMap((point) => [point.avg_price, point.median_price, point.min_price])
    .filter((value): value is number => typeof value === 'number')
  if (values.length === 0) {
    return { min: 0, max: 1 }
  }
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) {
    return { min: min - 1, max: max + 1 }
  }
  return { min, max }
})

function resolveX(index: number) {
  if (validPoints.value.length <= 1) return chartWidth / 2
  const usableWidth = chartWidth - paddingX * 2
  return paddingX + (usableWidth / (validPoints.value.length - 1)) * index
}

function resolveY(value: number) {
  const usableHeight = plotBottom - plotTop
  const ratio = (value - valueRange.value.min) / (valueRange.value.max - valueRange.value.min)
  return plotBottom - ratio * usableHeight
}

// 极值标记的文字锚点：首尾两个点靠边，居中锚点会让文字伸出画布，改成贴边对齐。
function labelAnchor(index: number) {
  if (validPoints.value.length <= 1) return 'middle'
  if (index === 0) return 'start'
  if (index === validPoints.value.length - 1) return 'end'
  return 'middle'
}

function labelX(index: number) {
  const anchor = labelAnchor(index)
  const x = resolveX(index)
  if (anchor === 'start') return x + 6
  if (anchor === 'end') return x - 6
  return x
}

function buildPath(values: Array<number | null>) {
  const commands = values
    .map((value, index) => {
      if (value === null || value === undefined) return null
      const prefix = index === 0 ? 'M' : 'L'
      return `${prefix} ${resolveX(index)} ${resolveY(value)}`
    })
    .filter(Boolean)
  return commands.join(' ')
}

const avgPath = computed(() => buildPath(validPoints.value.map((point) => point.avg_price)))
const medianPath = computed(() => buildPath(validPoints.value.map((point) => point.median_price)))
// 每日最低价：当天 AI 推荐商品中价格最低的那一件，用于观察"底价"走势。
const minPath = computed(() =>
  buildPath(validPoints.value.map((point) => (typeof point.min_price === 'number' ? point.min_price : null)))
)
const areaPath = computed(() => {
  if (!avgPath.value || validPoints.value.length === 0) return ''
  const firstX = resolveX(0)
  const lastX = resolveX(validPoints.value.length - 1)
  return `${avgPath.value} L ${lastX} ${plotBottom} L ${firstX} ${plotBottom} Z`
})

interface ExtremePoint {
  index: number
  point: TrendPoint
}

// 最高价/最低价标记：以 AI 推荐商品的均价曲线为准，标出曲线中的极值点。
const highPoint = computed<ExtremePoint | null>(() => {
  const points = validPoints.value
  let best: ExtremePoint | null = null
  for (let index = 0; index < points.length; index += 1) {
    const point = points[index]
    if (!point || typeof point.avg_price !== 'number') continue
    if (!best || point.avg_price > (best.point.avg_price as number)) {
      best = { index, point }
    }
  }
  return best
})

const lowPoint = computed<ExtremePoint | null>(() => {
  const points = validPoints.value
  let best: ExtremePoint | null = null
  for (let index = 0; index < points.length; index += 1) {
    const point = points[index]
    if (!point || typeof point.avg_price !== 'number') continue
    if (!best || point.avg_price < (best.point.avg_price as number)) {
      best = { index, point }
    }
  }
  return best
})
</script>

<template>
  <div class="app-surface-subtle p-4">
    <div class="mb-1 flex flex-col gap-3 text-xs uppercase tracking-[0.22em] text-slate-500 sm:flex-row sm:items-center sm:justify-between">
      <span>Daily Price Curve</span>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-sky-600" />
          {{ t('results.chart.avgPrice') }}
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-amber-500" />
          {{ t('results.chart.medianPrice') }}
        </span>
        <span class="inline-flex items-center gap-1">
          <span class="h-2.5 w-2.5 rounded-full bg-emerald-600" />
          {{ t('results.chart.minPrice') }}
        </span>
      </div>
    </div>
    <p class="mb-3 text-[11px] normal-case tracking-normal text-slate-400">
      {{ t('results.chart.aiSourceNote') }}
    </p>

    <div v-if="validPoints.length === 0" class="rounded-2xl border border-dashed border-slate-200 bg-white/70 px-4 py-10 text-center text-sm text-slate-500">
      {{ t('results.chart.noTrend') }}
    </div>

    <div v-else>
      <svg :viewBox="`0 0 ${chartWidth} ${chartHeight}`" class="h-[240px] w-full" role="img" :aria-label="t('results.chart.noTrend')">
        <defs>
          <linearGradient id="avg-area-fill" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stop-color="#0284c7" stop-opacity="0.24" />
            <stop offset="100%" stop-color="#0284c7" stop-opacity="0" />
          </linearGradient>
        </defs>

        <g>
          <line
            v-for="index in 4"
            :key="index"
            :x1="paddingX"
            :x2="chartWidth - paddingX"
            :y1="plotTop + ((plotBottom - plotTop) / 3) * (index - 1)"
            :y2="plotTop + ((plotBottom - plotTop) / 3) * (index - 1)"
            stroke="#cbd5e1"
            stroke-dasharray="4 6"
          />
        </g>

        <path :d="areaPath" fill="url(#avg-area-fill)" />
        <path :d="avgPath" fill="none" stroke="#0284c7" stroke-width="4" stroke-linecap="round" />
        <path :d="medianPath" fill="none" stroke="#f59e0b" stroke-width="3" stroke-dasharray="8 6" stroke-linecap="round" />
        <path :d="minPath" fill="none" stroke="#059669" stroke-width="2.5" stroke-dasharray="2 5" stroke-linecap="round" />

        <g v-for="(point, index) in validPoints" :key="point.day">
          <circle :cx="resolveX(index)" :cy="resolveY(point.avg_price as number)" r="5" fill="#0284c7" />
          <circle :cx="resolveX(index)" :cy="resolveY(point.median_price as number)" r="4" fill="#f59e0b" />
          <circle
            v-if="typeof point.min_price === 'number'"
            :cx="resolveX(index)"
            :cy="resolveY(point.min_price)"
            r="3.5"
            fill="#059669"
          />
          <text
            :x="resolveX(index)"
            :y="chartHeight - 6"
            text-anchor="middle"
            fill="#64748b"
            font-size="12"
          >
            {{ point.day.slice(5) }}
          </text>
        </g>

        <!-- 最高价：预留出独立的顶部留白（plotTop），标记文字固定画在曲线区域上方，不会压到网格线或图例。 -->
        <g v-if="highPoint">
          <circle
            :cx="resolveX(highPoint.index)"
            :cy="resolveY(highPoint.point.avg_price as number)"
            r="7"
            fill="none"
            stroke="#e11d48"
            stroke-width="2.5"
          />
          <text
            :x="labelX(highPoint.index)"
            :y="resolveY(highPoint.point.avg_price as number) - 14"
            :text-anchor="labelAnchor(highPoint.index)"
            fill="#e11d48"
            font-size="12"
            font-weight="600"
          >
            {{ t('results.chart.highMark', { price: highPoint.point.avg_price }) }}
          </text>
        </g>

        <!-- 最低价：同理，独立的底部留白（extremeLabelGap）把标记文字和下方的日期坐标轴隔开。 -->
        <g v-if="lowPoint && lowPoint.index !== highPoint?.index">
          <circle
            :cx="resolveX(lowPoint.index)"
            :cy="resolveY(lowPoint.point.avg_price as number)"
            r="7"
            fill="none"
            stroke="#16a34a"
            stroke-width="2.5"
          />
          <text
            :x="labelX(lowPoint.index)"
            :y="resolveY(lowPoint.point.avg_price as number) + 20"
            :text-anchor="labelAnchor(lowPoint.index)"
            fill="#16a34a"
            font-size="12"
            font-weight="600"
          >
            {{ t('results.chart.lowMark', { price: lowPoint.point.avg_price }) }}
          </text>
        </g>
      </svg>
    </div>
  </div>
</template>
