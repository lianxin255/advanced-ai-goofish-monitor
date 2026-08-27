import { ref, onMounted } from 'vue'
import type {
  Task,
  TaskCreateResponse,
  TaskGenerateRequest,
  TaskUpdate,
  TaskQueueState,
} from '@/types/task.d.ts'
import * as taskApi from '@/api/tasks'
import { useWebSocket } from '@/composables/useWebSocket'

export function useTasks() {
  const tasks = ref<Task[]>([])
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  const stoppingTaskIds = ref<Set<number>>(new Set())
  const queue = ref<TaskQueueState>({ running: [], queued: [] })
  const { on } = useWebSocket()

  async function fetchTasks(options?: { silent?: boolean }) {
    if (!options?.silent) {
      isLoading.value = true
    }
    error.value = null
    try {
      tasks.value = await taskApi.getAllTasks()
    } catch (e) {
      if (e instanceof Error) {
        error.value = e
      }
      console.error(e)
    } finally {
      if (!options?.silent) {
        isLoading.value = false
      }
    }
  }

  async function fetchQueue() {
    try {
      queue.value = await taskApi.getTaskQueue()
    } catch (e) {
      console.error(e)
    }
  }

  // 根据队列状态计算某任务的执行状态（乐观更新之外的实时来源）
  function resolveExecutionStatus(task: Task): 'idle' | 'queued' | 'running' {
    if (task.execution_status) return task.execution_status
    return task.is_running ? 'running' : 'idle'
  }

  function queuePosition(taskId: number): number {
    const index = queue.value.queued.indexOf(taskId)
    return index === -1 ? -1 : index + 1
  }

  // Real-time updates
  on('tasks_updated', () => {
    fetchTasks({ silent: true })
  })

  on('task_status_changed', (data: { id: number; is_running: boolean; execution_status?: string }) => {
    const task = tasks.value.find((t) => t.id === data.id)
    if (task) {
      task.is_running = data.is_running
      if (data.execution_status) {
        task.execution_status = data.execution_status as Task['execution_status']
      }
    }
    fetchTasks({ silent: true })
  })

  on('task_queue_changed', (data: TaskQueueState) => {
    queue.value = data
    fetchTasks({ silent: true })
  })

  async function createTask(data: TaskGenerateRequest): Promise<TaskCreateResponse> {
    isLoading.value = true
    error.value = null
    try {
      return await taskApi.createTaskWithAI(data)
    } catch (e) {
      if (e instanceof Error) {
        error.value = e
      }
      console.error(e)
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function updateTask(taskId: number, data: TaskUpdate) {
    error.value = null
    try {
      const updatedTask = await taskApi.updateTask(taskId, data)
      const index = tasks.value.findIndex((task) => task.id === updatedTask.id)
      if (index >= 0) {
        tasks.value[index] = { ...tasks.value[index], ...updatedTask }
      } else {
        tasks.value.push(updatedTask)
      }
    } catch (e) {
      if (e instanceof Error) {
        error.value = e
      }
      console.error(e)
      throw e
    }
  }

  async function removeTask(taskId: number) {
    try {
      await taskApi.deleteTask(taskId)
      // Refresh the list after deleting
      await fetchTasks()
    } catch (e) {
      console.error(e)
      // Optionally, set the error ref to display it in the UI
      if (e instanceof Error) {
        error.value = e
      }
      throw e
    }
  }

  async function startTask(taskId: number) {
    isLoading.value = true
    const task = tasks.value.find((t) => t.id === taskId)
    const previousRunning = task?.is_running
    const previousStatus = task?.execution_status
    if (task) {
      // 乐观更新：点击后立刻显示已入队（串行队列下不会马上运行）
      task.execution_status = 'queued'
      task.is_running = false
    }
    try {
      await taskApi.startTask(taskId)
      await fetchQueue()
    } catch (e) {
      if (task) {
        if (previousRunning !== undefined) task.is_running = previousRunning
        if (previousStatus !== undefined) task.execution_status = previousStatus
      }
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function stopTask(taskId: number) {
    isLoading.value = true
    const next = new Set(stoppingTaskIds.value)
    next.add(taskId)
    stoppingTaskIds.value = next
    try {
      await taskApi.stopTask(taskId)
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    } finally {
      const cleaned = new Set(stoppingTaskIds.value)
      cleaned.delete(taskId)
      stoppingTaskIds.value = cleaned
      isLoading.value = false
    }
  }
  
  // Load tasks when the composable is first used in a component
  onMounted(() => {
    fetchTasks()
    fetchQueue()
  })

  return {
    tasks,
    isLoading,
    error,
    queue,
    fetchTasks,
    fetchQueue,
    resolveExecutionStatus,
    queuePosition,
    createTask,
    updateTask,
    removeTask,
    startTask,
    stopTask,
    stoppingTaskIds,
  }
}
