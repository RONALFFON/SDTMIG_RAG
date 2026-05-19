import dayjs from 'dayjs'
import type MockAdapter from 'axios-mock-adapter'

type Session = {
  id: string
  title: string
  updatedAt: string
}

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: Array<{ id: string; docName: string; snippet: string; score: number }>
}

const sessions: Session[] = [
  { id: 's-1001', title: '新员工入职制度问答', updatedAt: dayjs().subtract(10, 'minute').format('YYYY-MM-DD HH:mm') },
  { id: 's-1002', title: '产品手册总结', updatedAt: dayjs().subtract(1, 'day').format('YYYY-MM-DD HH:mm') },
  { id: 's-1003', title: '财务流程对比', updatedAt: dayjs().subtract(2, 'day').format('YYYY-MM-DD HH:mm') }
]

const messagesMap = new Map<string, Message[]>([
  ['s-1001', []],
  ['s-1002', []],
  ['s-1003', []]
])

/**
 * 注册聊天相关 Mock
 */
export function setupChatMock(mock: MockAdapter): void {
  mock.onGet('/api/rag/sessions').reply(200, sessions)

  mock.onPost('/api/rag/sessions').reply(() => {
    const item: Session = {
      id: `s-${Date.now()}`,
      title: '新建对话',
      updatedAt: dayjs().format('YYYY-MM-DD HH:mm')
    }
    sessions.unshift(item)
    messagesMap.set(item.id, [])
    return [200, item]
  })

  mock.onGet(/\/api\/rag\/sessions\/[^/]+\/messages/).reply((config) => {
    const parts = config.url?.split('/') || []
    const sessionId = parts[4]
    return [200, messagesMap.get(sessionId || '') || []]
  })

  mock.onPost('/api/rag/upload').reply(() => {
    return [
      200,
      {
        taskId: `task-${Date.now()}`,
        fileName: '示例文档.pdf',
        progress: 100,
        status: 'completed'
      }
    ]
  })

  mock.onPost('/api/rag/query').reply((config) => {
    const body = JSON.parse(config.data || '{}')
    const sessionId = body.sessionId || sessions[0].id
    const question = body.question || ''
    const replyContent = `你问的是：${question}\n\n这是沙箱环境返回的 Mock 回答，可用于前端联调演示。`
    const replyMessage: Message = {
      id: `m-${Date.now()}`,
      role: 'assistant',
      content: replyContent,
      timestamp: dayjs().toISOString(),
      sources: [
        {
          id: 'ref-1',
          docName: '员工手册.pdf',
          snippet: '请在入职首周完成账号开通、信息登记和培训学习。',
          score: 0.92
        }
      ]
    }
    const current = messagesMap.get(sessionId) || []
    current.push(
      {
        id: `m-user-${Date.now()}`,
        role: 'user',
        content: question,
        timestamp: dayjs().toISOString()
      },
      replyMessage
    )
    messagesMap.set(sessionId, current)
    return [200, { answer: replyContent, sources: replyMessage.sources }]
  })
}
