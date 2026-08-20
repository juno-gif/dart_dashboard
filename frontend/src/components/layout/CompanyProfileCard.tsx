'use client'
import { useCompanyProfile } from '@/hooks/use-company-profile'
import { Skeleton } from '@/components/ui/skeleton'

interface Props {
  corpCode: string | null
}

/** DART est_dt(YYYYMMDD) → "1969.01.13" */
function formatEstDt(estDt: string): string {
  if (!/^\d{8}$/.test(estDt)) return estDt
  return `${estDt.slice(0, 4)}.${estDt.slice(4, 6)}.${estDt.slice(6, 8)}`
}

function normalizeUrl(url: string): string {
  return /^https?:\/\//i.test(url) ? url : `https://${url}`
}

export function CompanyProfileCard({ corpCode }: Props) {
  const { data, isLoading, isError } = useCompanyProfile(corpCode)

  if (!corpCode || isError) return null

  if (isLoading) {
    return (
      <div className="rounded-lg border bg-muted/20 p-4 flex flex-wrap gap-x-6 gap-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-4 w-24" />
        ))}
      </div>
    )
  }

  if (!data) return null

  const fields: { label: string; value: string | null }[] = [
    { label: '설립일', value: data.est_dt ? formatEstDt(data.est_dt) : null },
    { label: '대표이사', value: data.ceo_nm },
    {
      label: '임직원수',
      value: data.employee_count
        ? `${data.employee_count.toLocaleString()}명${data.employee_count_source === 'nps' ? ' (국민연금 추정)' : ''}`
        : null,
    },
    { label: '사업장주소', value: data.adres },
  ]

  const hasAnyField = fields.some((f) => f.value) || data.hm_url
  if (!hasAnyField) return null

  return (
    <div className="rounded-lg border bg-muted/20 p-4 flex flex-wrap gap-x-6 gap-y-1.5 text-sm">
      {fields.map(
        (f) =>
          f.value && (
            <div key={f.label} className="flex items-baseline gap-1.5">
              <span className="text-muted-foreground shrink-0">{f.label}</span>
              <span className="text-foreground">{f.value}</span>
            </div>
          )
      )}
      {data.hm_url && (
        <div className="flex items-baseline gap-1.5">
          <span className="text-muted-foreground shrink-0">홈페이지</span>
          <a
            href={normalizeUrl(data.hm_url)}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-500 hover:underline"
          >
            {data.hm_url}
          </a>
        </div>
      )}
    </div>
  )
}
