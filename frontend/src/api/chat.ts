import http from '@/utils/request'

export interface ChatSession {
  id: string
  title: string
  updatedAt: string
}

export interface SourceItem {
  id: string
  docName: string
  snippet: string
  score: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: SourceItem[]
}

export interface UploadTask {
  taskId: string
  fileName: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
}

/**
 * 获取会话列表
 */
export async function getSessionsApi(): Promise<ChatSession[]> {
  const { data } = await http.get('/api/rag/sessions')
  return data
}

/**
 * 创建新会话
 */
export async function createSessionApi(): Promise<ChatSession> {
  const { data } = await http.post('/api/rag/sessions')
  return data
}

/**
 * 获取单个会话消息
 */
export async function getSessionMessagesApi(sessionId: string): Promise<ChatMessage[]> {
  const { data } = await http.get(`/api/rag/sessions/${sessionId}/messages`)
  return data
}

/**
 * 提问接口
 */
export async function queryApi(payload: {
  sessionId: string
  question: string
  taskIds?: string[]
}): Promise<{ answer: string; sources: SourceItem[] }> {
  const { data } = await http.post('/api/rag/query', payload)
  return data
}

/**
 * 上传文档
 */
export async function uploadApi(file: File): Promise<UploadTask> {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await http.post('/api/rag/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return data
}
