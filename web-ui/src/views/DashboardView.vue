<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useDashboard } from '@/composables/useDashboard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import PriceTrendChart from '@/components/results/PriceTrendChart.vue'
import { LayoutDashboard, Wallet } from 'lucide-vue-next'

const router = useRouter()
const { t } = useI18n()
const { taskSummaries, error } = useDashboard()

const priceOverviewRows = computed(() =>
  [...taskSummaries.value].sort((a, b) => {
    const aHasPrice = a.history_avg_price !== null ? 1 : 0
    const bHasPrice = b.history_avg_price !== null ? 1 : 0
    if (aHasPrice !== bHasPrice) return bHasPrice - aHasPrice
    return a.task_name.localeCompare(b.task_name)
  })
)

function openTaskPrice(item: { filename: string | null }) {
  if (item.filename) {
    router.push({ name: 'Results', query: { file: item.filename } })
  }
}

function goCreateTask() {
  router.push({
    name: 'Tasks',
    query: { create: '1' },
  })
}
</script>

<template>
  <div class="space-y-8 animate-fade-in">
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-3xl font-black text-slate-800 tracking-tight flex items-center gap-3">
          <LayoutDashboard class="w-8 h-8 text-primary" />
          {{ t('dashboard.title') }}
        </h1>
        <p class="text-slate-500 mt-1 font-medium">
          {{ t('dashboard.description') }}
        </p>
      </div>
      <div class="flex items-center gap-3">
        <Button class="shadow-md shadow-primary/20" @click="goCreateTask">
          {{ t('dashboard.createTask') }}
        </Button>
      </div>
    </div>
    <div v-if="error" class="app-alert-error" role="alert">
      {{ error.message }}
    </div>
    <Card class="app-surface border-none">
      <CardHeader class="border-b border-slate-100/60 pb-5">
        <CardTitle class="text-lg font-bold text-slate-800 flex items-center gap-2">
          <Wallet class="w-5 h-5 text-emerald-500" />
          {{ t('dashboard.priceOverview.title') }}
        </CardTitle>
        <p class="mt-1 text-sm text-slate-500">{{ t('dashboard.priceOverview.description') }}</p>
      </CardHeader>
      <CardContent class="p-6">
        <div v-if="priceOverviewRows.length === 0" class="px-6 py-10 text-center text-sm text-slate-500">
          {{ t('dashboard.priceOverview.empty') }}
        </div>
        <div v-else class="grid gap-5 lg:grid-cols-2">
          <div
            v-for="item in priceOverviewRows"
            :key="item.task_id ?? item.task_name"
            class="rounded-2xl border border-slate-200/70 bg-white/70 p-4 shadow-sm transition-colors"
            :class="item.filename ? 'hover:border-primary/40 cursor-pointer' : ''"
            @click="openTaskPrice(item)"
          >
            <div class="flex items-center justify-between gap-4">
              <div class="min-w-0">
                <p class="text-sm font-bold text-slate-700 truncate">{{ item.task_name }}</p>
                <p class="text-[11px] text-slate-400 truncate">{{ item.keyword }}</p>
              </div>
              <div class="text-right shrink-0">
                <p class="text-lg font-semibold text-slate-900">
                  {{ item.history_avg_price !== null ? `¥${item.history_avg_price}` : t('dashboard.priceOverview.noHistory') }}
                </p>
                <p class="text-[11px] text-slate-400">
                  <template v-if="item.history_sample_count">
                    {{ t('dashboard.priceOverview.sampleLabel', { count: item.history_sample_count }) }}
                  </template>
                </p>
              </div>
            </div>
            <PriceTrendChart class="mt-3" :points="item.history_daily_trend" />
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
