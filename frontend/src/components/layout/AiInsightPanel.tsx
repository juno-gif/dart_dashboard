'use client'

/**
 * AI 인사이트 패널 — Story 6.2
 * POST /api/v1/analysis-sets/{id}/ai-summary 를 통해 LLM 재무 요약 및 Q&A 제공
 * [Source: architecture.md - Frontend Architecture]
 */
import { useEffect, useRef, useState } from 'react'
import { Loader2, X } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { requestAiSummary } from '@/lib/api'

interface AiInsightPanelProps {
  setId: string
  setName: string
  isOpen: boolean
  onClose: () => void
}

interface Message {
  role: 'assistant' | 'user'
  content: string
}

export function AiInsightPanel({ setId, setName, isOpen, onClose }: AiInsightPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [hasError, setHasError] = useState(false)
  const [lastFailedQuestion, setLastFailedQuestion] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const summaryMutation = useMutation({
    mutationFn: () => requestAiSummary(setId),
    onSuccess: (data) => {
      setHasError(false)
      setMessages([{ role: 'assistant', content: data.content }])
    },
    onError: () => {
      setHasError(true)
    },
  })

  const questionMutation = useMutation({
    mutationFn: (q: string) => requestAiSummary(setId, q),
    onSuccess: (data) => {
      setLastFailedQuestion(null)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.content }])
    },
    onError: (_err, variables) => {
      setLastFailedQuestion(variables)
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'AI 요약을 불러올 수 없습니다. 잠시 후 재시도해 주세요.' },
      ])
    },
  })

  useEffect(() => {
    if (isOpen) {
      // 패널 열릴 때: 상태 초기화 후 초기 요약 요청
      setHasError(false)
      setLastFailedQuestion(null)
      summaryMutation.mutate()
    } else {
      // 패널 닫힐 때: 모든 상태 초기화
      setMessages([])
      setQuestion('')
      setHasError(false)
      setLastFailedQuestion(null)
    }
    // summaryMutation 참조는 의도적으로 의존성에서 제외 (isOpen 변경 시에만 실행)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = question.trim()
    if (!q || questionMutation.isPending) return
    setMessages((prev) => [...prev, { role: 'user', content: q }])
    setQuestion('')
    questionMutation.mutate(q)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col border-l border-border bg-background shadow-xl">
      {/* 헤더 */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div>
          <p className="text-sm font-semibold">AI 인사이트</p>
          <p className="text-xs text-muted-foreground truncate max-w-[280px]">{setName}</p>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 hover:bg-accent text-muted-foreground hover:text-foreground"
          title="닫기"
        >
          <X size={16} />
        </button>
      </div>

      {/* 메시지 영역 */}
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {summaryMutation.isPending && messages.length === 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 size={14} className="animate-spin" />
            <span>AI가 재무 데이터를 분석 중입니다...</span>
          </div>
        )}

        {hasError && messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-destructive">
              AI 요약을 불러올 수 없습니다. 잠시 후 재시도해 주세요.
            </p>
            <button
              onClick={() => {
                setHasError(false)
                summaryMutation.mutate()
              }}
              className="text-xs px-3 py-1.5 rounded border border-border hover:bg-accent transition-colors"
            >
              재시도
            </button>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-sm ${
              msg.role === 'user'
                ? 'ml-8 bg-primary text-primary-foreground'
                : 'mr-8 bg-muted text-foreground'
            }`}
          >
            <p className="whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}

        {questionMutation.isPending && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 size={14} className="animate-spin" />
            <span>답변 생성 중...</span>
          </div>
        )}

        {lastFailedQuestion && !questionMutation.isPending && (
          <button
            onClick={() => {
              setLastFailedQuestion(null)
              questionMutation.mutate(lastFailedQuestion)
            }}
            className="text-xs px-3 py-1.5 rounded border border-border hover:bg-accent transition-colors"
          >
            재시도
          </button>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 질의 입력 */}
      <form onSubmit={handleSubmit} className="border-t border-border px-4 py-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="재무 데이터에 대해 질문하세요..."
            disabled={questionMutation.isPending || summaryMutation.isPending}
            className="flex-1 rounded border border-border bg-background px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!question.trim() || questionMutation.isPending || summaryMutation.isPending}
            className="rounded bg-primary px-3 py-1.5 text-xs text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {questionMutation.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              '전송'
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
