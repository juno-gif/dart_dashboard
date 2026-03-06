'use client'
import { useState } from 'react'

interface Props {
  chartRef: React.RefObject<HTMLDivElement | null>
  filename: string // 예: "삼성전자_2026-03-05"
}

export function DownloadButton({ chartRef, filename }: Props) {
  const [isCapturing, setIsCapturing] = useState(false)

  const handleDownload = async () => {
    if (!chartRef.current) return
    setIsCapturing(true)
    try {
      const html2canvas = (await import('html2canvas')).default
      const canvas = await html2canvas(chartRef.current, { backgroundColor: '#ffffff' })
      const link = document.createElement('a')
      link.download = `${filename}.png`
      link.href = canvas.toDataURL('image/png')
      link.click()
    } finally {
      setIsCapturing(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={isCapturing}
      className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded border border-gray-200 hover:border-gray-400 disabled:opacity-50"
      aria-label="차트 이미지 다운로드"
    >
      {isCapturing ? '캡처 중...' : '↓ PNG'}
    </button>
  )
}
