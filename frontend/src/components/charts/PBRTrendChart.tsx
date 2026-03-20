'use client'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Skeleton } from '@/components/ui/skeleton'
import type { ValuationData } from '@/lib/api'

interface Props {
  data: ValuationData | undefined
  isLoading: boolean
}

export function PBRTrendChart({ data, isLoading }: Props) {
  if (isLoading) {
    return <Skeleton className="h-52 w-full rounded-xl mt-4" />
  }

  if (!data || data.yearly.length === 0) return null

  return (
    <div className="mt-6">
      <h3 className="text-sm font-medium text-muted-foreground mb-2">PBR / PER 추이</h3>
      <div className="h-52 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.yearly} margin={{ top: 8, right: 24, bottom: 0, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 11 }} width={40} />
            <Tooltip
              formatter={(value, name) => [
                value != null ? Number(value).toFixed(2) : '-',
                name === 'pbr' ? 'PBR' : name === 'per' ? 'PER' : String(name ?? ''),
              ]}
            />
            <Legend formatter={(v) => (v === 'pbr' ? 'PBR' : 'PER')} />
            {data.current_pbr != null && (
              <ReferenceLine
                y={data.current_pbr}
                stroke="#2563eb"
                strokeDasharray="4 2"
                label={{ value: `현재 ${data.current_pbr.toFixed(2)}x`, fontSize: 11, fill: '#2563eb', position: 'right' }}
              />
            )}
            <Line dataKey="pbr" name="pbr" stroke="#2563eb" strokeWidth={2} dot />
            <Line dataKey="per" name="per" stroke="#f59e0b" strokeWidth={2} dot />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
