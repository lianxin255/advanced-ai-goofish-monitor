<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Task, TaskQueueState } from '@/types/task.d.ts'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Square, ListOrdered } from 'lucide-vue-next'

const props = defineProps<{
  queue: TaskQueueState
  tasks: Task[]
}>()

const emit = defineEmits<{
  (e: 'stop-task', taskId: number): void
}>()

const { t } = useI18n()

const taskByName = computed(() => {
  const map = new Map<number, Task>()
  for (const task of props.tasks) map.set(task.id, task)
  return map
})

const runningTasks = computed(() =>
  (props.queue.running ?? []).map((id) => taskByName.value.get(id)).filter(Boolean) as Task[]
)

const queuedTasks = computed(() =>
  (props.queue.queued ?? []).map((id) => taskByName.value.get(id)).filter(Boolean) as Task[]
)

const hasItems = computed(() => runningTasks.value.length > 0 || queuedTasks.value.length > 0)
</script>

<template>
  <div
    v-if="hasItems"
    class="app-surface overflow-hidden animate-fade-in border-amber-100"
  >
    <div class="flex items-center gap-2 border-b border-slate-100/60 px-4 py-3">
      <ListOrdered class="h-4 w-4 text-amber-500" />
      <h2 class="text-sm font-bold text-slate-800">{{ t('tasks.queue.title') }}</h2>
      <span class="text-[11px] font-medium text-slate-400">
        {{ t('tasks.queue.hint') }}
      </span>
    </div>

    <div class="space-y-2 p-4">
      <div v-if="runningTasks.length" class="space-y-1.5">
        <p class="text-[10px] font-black uppercase tracking-widest text-emerald-600">
          {{ t('tasks.queue.running') }}
        </p>
        <div
          v-for="task in runningTasks"
          :key="`running-${task.id}`"
          class="flex items-center justify-between gap-3 rounded-xl border border-emerald-200/70 bg-emerald-50/60 px-3 py-2"
        >
          <div class="flex min-w-0 items-center gap-2">
            <span class="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
            <span class="truncate text-sm font-semibold text-slate-700">{{ task.task_name }}</span>
          </div>
          <Button
            size="sm"
            variant="destructive"
            class="h-7 px-2.5 text-[11px]"
            @click="emit('stop-task', task.id)"
          >
            <Square class="mr-1 h-3 w-3 fill-current" />
            {{ t('tasks.table.stop') }}
          </Button>
        </div>
      </div>

      <div v-if="queuedTasks.length" class="space-y-1.5">
        <p class="text-[10px] font-black uppercase tracking-widest text-amber-600">
          {{ t('tasks.queue.waiting') }} ({{ queuedTasks.length }})
        </p>
        <div
          v-for="(task, index) in queuedTasks"
          :key="`queued-${task.id}`"
          class="flex items-center justify-between gap-3 rounded-xl border border-amber-200/70 bg-amber-50/50 px-3 py-2"
        >
          <div class="flex min-w-0 items-center gap-2">
            <Badge
              variant="outline"
              class="border-amber-200 bg-white text-[10px] font-black text-amber-600"
            >
              #{{ index + 1 }}
            </Badge>
            <span class="truncate text-sm font-medium text-slate-700">{{ task.task_name }}</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            class="h-7 border-amber-200 px-2.5 text-[11px] text-amber-700 hover:bg-amber-100"
            @click="emit('stop-task', task.id)"
          >
            <Square class="mr-1 h-3 w-3 fill-current" />
            {{ t('tasks.table.cancelQueue') }}
          </Button>
        </div>
      </div>
    </div>
  </div>
</template>
