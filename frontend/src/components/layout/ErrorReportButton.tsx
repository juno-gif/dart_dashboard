'use client'
import { useState, useRef } from 'react'
import emailjs from '@emailjs/browser'
import html2canvas from 'html2canvas'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import type { FinancialType } from '@/types'

const EMAILJS_SERVICE_ID = 'service_p0wi75f'
const EMAILJS_TEMPLATE_ID = 'template_elvl9q9'
const EMAILJS_PUBLIC_KEY = '0P_TdyqxW0YyfskP0'

interface Props {
  companyName: string
  chartContainerRef: React.RefObject<HTMLDivElement | null>
  chartType: FinancialType
  setChartType: (type: FinancialType) => void
}

type Status = 'idle' | 'capturing' | 'sending' | 'done' | 'error'

export function ErrorReportButton({
  companyName,
  chartContainerRef,
  chartType,
  setChartType,
}: Props) {
  const [open, setOpen] = useState(false)
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState<Status>('idle')
  const screenshots = useRef<{ pl: string; bs: string; cf: string } | null>(null)

  const captureTab = async (type: FinancialType): Promise<string> => {
    if (!chartContainerRef.current) return ''
    setChartType(type)
    await new Promise((r) => setTimeout(r, 700))
    try {
      const canvas = await html2canvas(chartContainerRef.current, {
        scale: 0.4,
        useCORS: true,
        backgroundColor: '#ffffff',
        logging: false,
      })
      return canvas.toDataURL('image/jpeg', 0.5)
    } catch {
      return ''
    }
  }

  const handleOpen = async () => {
    setOpen(true)
    setStatus('capturing')
    const originalType = chartType
    try {
      const pl = await captureTab('pl')
      const bs = await captureTab('bs')
      const cf = await captureTab('cf')
      screenshots.current = { pl, bs, cf }
    } finally {
      setChartType(originalType)
    }
    setStatus('idle')
  }

  const handleSend = async () => {
    setStatus('sending')
    try {
      await emailjs.send(
        EMAILJS_SERVICE_ID,
        EMAILJS_TEMPLATE_ID,
        {
          company_name: companyName,
          description: description || '(내용 없음)',
          timestamp: new Date().toLocaleString('ko-KR'),
          screenshot_pl: screenshots.current?.pl ?? '',
          screenshot_bs: screenshots.current?.bs ?? '',
          screenshot_cf: screenshots.current?.cf ?? '',
        },
        EMAILJS_PUBLIC_KEY,
      )
      setStatus('done')
      setTimeout(() => {
        setOpen(false)
        setStatus('idle')
        setDescription('')
      }, 1500)
    } catch {
      setStatus('error')
    }
  }

  const handleClose = () => {
    if (status === 'capturing' || status === 'sending') return
    setOpen(false)
    setStatus('idle')
    setDescription('')
  }

  return (
    <>
      <button
        onClick={handleOpen}
        className="text-xs text-muted-foreground hover:text-destructive transition-colors border rounded-md px-3 py-1.5"
      >
        🚨 오류 신고
      </button>

      <Dialog open={open} onOpenChange={handleClose}>
        <DialogContent showCloseButton={status !== 'capturing' && status !== 'sending'}>
          <DialogHeader>
            <DialogTitle>오류 신고</DialogTitle>
          </DialogHeader>

          {status === 'capturing' && (
            <div className="flex flex-col items-center gap-3 py-6 text-sm text-muted-foreground">
              <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
              <p>화면을 캡처하는 중입니다...</p>
            </div>
          )}

          {(status === 'idle' || status === 'sending' || status === 'error') && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                <strong className="text-foreground">{companyName}</strong>의 재무 데이터
                오류를 운영자에게 신고합니다. 3개 탭 화면이 자동으로 첨부됩니다.
              </p>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  오류 내용 (선택)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="예: 2023년 매출 데이터가 이상합니다."
                  className="w-full border rounded-md px-3 py-2 text-sm resize-none h-24 bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                  disabled={status === 'sending'}
                />
              </div>
              {status === 'error' && (
                <p className="text-xs text-destructive">
                  전송에 실패했습니다. 잠시 후 다시 시도해주세요.
                </p>
              )}
            </div>
          )}

          {status === 'done' && (
            <div className="flex flex-col items-center gap-2 py-6">
              <p className="text-green-600 font-medium">✓ 신고가 접수되었습니다.</p>
              <p className="text-xs text-muted-foreground">빠르게 검토 후 수정하겠습니다.</p>
            </div>
          )}

          {(status === 'idle' || status === 'sending' || status === 'error') && (
            <DialogFooter>
              <Button variant="outline" onClick={handleClose} disabled={status === 'sending'}>
                취소
              </Button>
              <Button onClick={handleSend} disabled={status === 'sending'}>
                {status === 'sending' ? '전송 중...' : '신고하기'}
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
