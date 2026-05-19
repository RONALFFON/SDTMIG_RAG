import dayjs from 'dayjs'
import { defineStore } from 'pinia'
import {
  createSessionApi,
  getSessionMessagesApi,
  getSessionsApi,
  queryApi,
  uploadApi,
  type ChatMessage,
  type ChatSession,
  type UploadTask
} from '@/api/chat'

type RenderMode = 'markdown' | 'text'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [] as ChatSession[],
    currentSessionId: '' as string,
    messages: [] as ChatMessage[],
    uploadTasks: [] as UploadTask[],
    enterToSend: true,
    renderMode: 'markdown' as RenderMode
  }),
  actions: {
    /**
     * 获取会话列表
     */
    async fetchSessions(): Promise<void> {
      this.sessions = await getSessionsApi()
      if (!this.currentSessionId && this.sessions.length > 0) {
        this.currentSessionId = this.sessions[0].id
        await this.switchSession(this.currentSessionId)
      }
    },

    /**
     * 新建会话并切换
     */
    async createSession(): Promise<void> {
      const session = await createSessionApi()
      this.sessions.unshift(session)
      this.currentSessionId = session.id
      this.messages = []
    },

    /**
     * 切换会话并加载消息
     */
    async switchSession(sessionId: string): Promise<void> {
      this.currentSessionId = sessionId
      this.messages = await getSessionMessagesApi(sessionId)
    },

    /**
     * 上传文件
     */
    async uploadFile(file: File): Promise<void> {
      const task = await uploadApi(file)
      this.uploadTasks.unshift(task)
    },

    /**
     * 发送消息
     */
    async sendMessage(question: string): Promise<void> {
      if (!this.currentSessionId) {
        await this.createSession()
      }

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: question,
        timestamp: dayjs().toISOString()
      }
      const assistantPlaceholder: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '',
        timestamp: dayjs().toISOString(),
        sources: []
      }

      this.messages.push(userMessage, assistantPlaceholder)
      const taskIds = this.uploadTasks
        .filter((task) => task.status === 'completed')
        .map((task) => task.taskId)

      const result = await queryApi({
        sessionId: this.currentSessionId,
        question,
        taskIds
      })

      assistantPlaceholder.content = result.answer
      assistantPlaceholder.sources = result.sources

      const currentSession = this.sessions.find((item) => item.id === this.currentSessionId)
      if (currentSession) {
        currentSession.updatedAt = dayjs().format('YYYY-MM-DD HH:mm')
      }
    },

    /**
     * 更新回车发送偏好
     */
    setEnterToSend(value: boolean): void {
      this.enterToSend = value
    },

    /**
     * 更新回答渲染模式
     */
    setRenderMode(mode: RenderMode): void {
      this.renderMode = mode
    },

    /**
     * 移除上传任务
     */
    removeUploadTask(taskId: string): void {
      this.uploadTasks = this.uploadTasks.filter((item) => item.taskId !== taskId)
    }
  }
})
