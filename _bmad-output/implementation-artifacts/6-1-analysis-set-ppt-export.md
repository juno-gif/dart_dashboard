# Story 6.1: 분석 세트 PPT 내보내기

Status: done

## Story

As a Builder,
I want to export an analysis set as a PowerPoint file,
so that I can use the financial comparison results directly in presentations without manual re-creation.

## Acceptance Criteria

1. **[PPT 내보내기 버튼]** Builder/Admin이 분석 세트 목록에서 PPT 내보내기 버튼을 클릭하면, `POST /api/v1/analysis-sets/{id}/export/ppt`가 호출되며 버튼에 로딩 인디케이터(`isPending`)가 표시되어야 한다

2. **[자동 다운로드]** PPT 파일이 생성 완료되면 `{분석세트명}_{YYYY-MM-DD}.pptx` 형식으로 파일이 자동 다운로드되어야 한다. 성공 Toast "PPT 파일이 다운로드되었습니다" 3초 자동 소멸

3. **[슬라이드 구성]** 생성된 PPT에는 다음 슬라이드가 포함되어야 한다:
   - Slide 1: 제목 슬라이드 (분석 세트명, 생성일, 기업 목록)
   - Slide 2~N: 기업별 P&L 트렌드 (매출·영업이익·순이익 바 차트)
   - Slide N+1: 전체 기업 매출 비교 슬라이드

4. **[접근 제어]** Builder는 본인 소유 분석 세트만 내보낼 수 있고, Admin은 모든 세트 내보내기 가능. 권한 없는 접근 시 403 반환

5. **[오류 처리]** PPT 생성 중 서버 오류 시 Red Toast "내보내기에 실패했습니다. 잠시 후 재시도해 주세요" (수동 닫기)

## Tasks / Subtasks

- [x] Task 1: Backend — `python-pptx` 의존성 추가 (AC: #3)
  - [x] 1.1 `backend/requirements.txt`에 `python-pptx>=1.0.0` 추가

- [x] Task 2: Backend — PPT 생성 서비스 구현 (AC: #3)
  - [x] 2.1 `backend/app/services/ppt_service.py` 신규 생성
  - [x] 2.2 `generate_analysis_ppt(set_name, companies, financials_by_corp)` 함수 구현
    - Slide 1: 제목 슬라이드 (set_name, 날짜, 기업명 목록)
    - Slide 2~N: 기업별 P&L 바 차트 (`prs.add_chart` — CHART_TYPE.BAR_CLUSTERED, 매출/영업이익/순이익)
    - Slide N+1: 다기업 매출 비교 바 차트
  - [x] 2.3 `Presentation` 객체를 `io.BytesIO`에 저장 후 bytes 반환

- [x] Task 3: Backend — export/ppt 엔드포인트 추가 (AC: #1, #4)
  - [x] 3.1 `backend/app/api/v1/analysis_sets.py`에 엔드포인트 추가
  - [x] 3.2 분석 세트 조회 + 소유권 체크 (기존 share_analysis_set 패턴 동일)
  - [x] 3.3 각 corp_code별 `get_pl_data(corp_code, years=5)` 호출 (`financial_service.py` 재사용)
  - [x] 3.4 `generate_analysis_ppt()` 호출 → bytes 획득
  - [x] 3.5 `StreamingResponse` 반환 (RFC 5987 UTF-8 인코딩 파일명 적용)

- [x] Task 4: Backend — 테스트 작성 (AC: #1, #4, #5)
  - [x] 4.1 `backend/tests/test_ppt_export.py` 신규 생성
  - [x] 4.2 `test_export_ppt_success` — Builder가 본인 세트 내보내기 → 200, Content-Type 검증
  - [x] 4.3 `test_export_ppt_forbidden` — 타인 세트 내보내기 → 403
  - [x] 4.4 `test_export_ppt_not_found` — 존재하지 않는 set_id → 404

- [x] Task 5: Frontend — `lib/api.ts` 업데이트 (AC: #1, #2)
  - [x] 5.1 `apiPostBlob(path)` 함수 추가 (binary POST response용, `res.blob()` 반환)
  - [x] 5.2 `exportAnalysisSetPpt(setId: string): Promise<Blob>` 함수 추가

- [x] Task 6: Frontend — `AnalysisSetItem.tsx` PPT 버튼 추가 (AC: #1, #2, #5)
  - [x] 6.1 `AnalysisSetItem.tsx`에 PPT 내보내기 버튼 추가 (ShareDialog 옆, `canEdit` 조건 동일)
  - [x] 6.2 `useMutation` — `exportAnalysisSetPpt(set.id)` 호출
  - [x] 6.3 `onSuccess`: Blob → `URL.createObjectURL` → `<a download>` 클릭 → `URL.revokeObjectURL` → toast success
  - [x] 6.4 `onError`: toast error (수동 닫기, `duration: undefined`)
  - [x] 6.5 버튼: `isPending` 시 `<Loader2>` 스피너 + `disabled`

- [x] Task 7: `npm run build` + pytest 전체 통과 확인

## Dev Notes

### 핵심 설계 결정

**PPT 라이브러리**: `python-pptx` 선택
- 순수 Python, 서버사이드 생성, 추가 런타임 불필요
- `prs.slides.add_slide()` + `prs.add_chart()` API로 바 차트 직접 생성
- matplotlib 불필요 (의존성 최소화)

**재무 데이터 흐름**: 기존 `financial_service.py`의 `get_pl_data(corp_code, years=5)` 재사용
- `List[FinancialStatement]` 반환 (account_key: revenue/operating_profit/net_income, amount: 원 단위)
- PPT 내 표시 시 억 단위 변환: `amount / 100_000_000`

**Binary 파일 다운로드 패턴** (프론트):
```typescript
// lib/api.ts — apiGetBlob 패턴
export async function apiGetBlob(path: string): Promise<Blob> {
  const token = await getToken()
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ error: 'UNKNOWN_ERROR', status_code: res.status }))
    throw error
  }
  return res.blob()
}
```

**다운로드 트리거 패턴**:
```typescript
// onSuccess 핸들러
onSuccess: (blob) => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${set.name}_${new Date().toISOString().slice(0, 10)}.pptx`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('PPT 파일이 다운로드되었습니다', { duration: 3000 })
}
```

### Backend 엔드포인트 상세 설계

```python
# analysis_sets.py 추가 (파일 하단)
from fastapi.responses import StreamingResponse
import io
from datetime import date

from app.services.ppt_service import generate_analysis_ppt
from app.services.financial_service import get_pl_data

@router.post("/analysis-sets/{set_id}/export/ppt")
async def export_analysis_set_ppt(set_id: str, user=Depends(get_current_user)):
    """분석 세트 PPT 내보내기 (Builder: 본인 소유만, Admin: 전체)"""
    supabase = get_supabase_client()

    # 세트 조회 + 소유권 체크 (share_analysis_set 패턴 동일)
    res = supabase.table("analysis_sets").select("*").eq("id", set_id).execute()
    if not res.data:
        raise HTTPException(404, detail={"error": "ANALYSIS_SET_NOT_FOUND", ...})
    existing = res.data[0]
    role = get_user_role(user.id)
    if role != "admin" and existing["owner_id"] != user.id:
        raise HTTPException(403, detail={"error": "INSUFFICIENT_PERMISSION", ...})

    # 각 기업 PL 데이터 수집
    financials_by_corp = {}
    for corp_code in existing["company_codes"]:
        try:
            financials_by_corp[corp_code] = get_pl_data(corp_code, years=5)
        except Exception:
            financials_by_corp[corp_code] = []  # 데이터 없어도 PPT 생성 계속

    # PPT 생성
    pptx_bytes = generate_analysis_ppt(
        set_name=existing["name"],
        company_codes=existing["company_codes"],
        financials_by_corp=financials_by_corp,
    )

    filename = f"{existing['name']}_{date.today().isoformat()}.pptx"
    return StreamingResponse(
        io.BytesIO(pptx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

### ppt_service.py 설계

```python
# backend/app/services/ppt_service.py
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE
import io
from datetime import date

def generate_analysis_ppt(set_name: str, company_codes: list[str], financials_by_corp: dict) -> bytes:
    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # Slide 1: 제목
    _add_title_slide(prs, set_name, company_codes)

    # Slide 2~N: 기업별 PL 트렌드
    for corp_code in company_codes:
        data = financials_by_corp.get(corp_code, [])
        _add_company_pl_slide(prs, corp_code, data)

    # Slide N+1: 매출 비교 (all companies)
    _add_comparison_slide(prs, company_codes, financials_by_corp)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()

def _add_title_slide(prs, set_name, company_codes):
    slide_layout = prs.slide_layouts[0]  # Title Slide
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = set_name
    slide.placeholders[1].text = f"생성일: {date.today().isoformat()}\n기업: {', '.join(company_codes)}"

def _add_company_pl_slide(prs, corp_code, financials):
    # 연도별 그룹핑
    by_year = {}
    for f in financials:
        by_year.setdefault(f.bsns_year, {})[f.account_key] = (f.amount or 0) / 100_000_000
    years = sorted(by_year.keys())

    slide_layout = prs.slide_layouts[5]  # Blank
    slide = prs.slides.add_slide(slide_layout)
    # 제목 텍스트박스
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.5))
    txBox.text_frame.text = f"{corp_code} P&L 트렌드 (억원)"

    if not years:
        return

    chart_data = ChartData()
    chart_data.categories = years
    chart_data.add_series("매출", [by_year[y].get("revenue", 0) for y in years])
    chart_data.add_series("영업이익", [by_year[y].get("operating_profit", 0) for y in years])
    chart_data.add_series("순이익", [by_year[y].get("net_income", 0) for y in years])

    slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(1), Inches(12), Inches(6), chart_data
    )

def _add_comparison_slide(prs, company_codes, financials_by_corp):
    # 가장 최근 연도 매출 비교
    latest_revenues = {}
    for corp_code in company_codes:
        data = financials_by_corp.get(corp_code, [])
        by_year = {}
        for f in data:
            by_year.setdefault(f.bsns_year, {})[f.account_key] = (f.amount or 0) / 100_000_000
        if by_year:
            latest_year = sorted(by_year.keys())[-1]
            latest_revenues[corp_code] = by_year[latest_year].get("revenue", 0)

    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(0.5))
    txBox.text_frame.text = "기업별 매출 비교 (억원, 최근 연도)"

    if not latest_revenues:
        return

    chart_data = ChartData()
    chart_data.categories = list(latest_revenues.keys())
    chart_data.add_series("매출", list(latest_revenues.values()))
    slide.shapes.add_chart(
        XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.5), Inches(1), Inches(12), Inches(6), chart_data
    )
```

### 테스트 설계

```python
# tests/test_ppt_export.py
# 핵심: python-pptx 생성은 ppt_service를 mock, 200 + Content-Type 체크
from unittest.mock import patch, MagicMock

def test_export_ppt_success(builder_client):
    mock_supabase = _mock_supabase_with_set(owner_is_current=True)
    with patch("app.api.v1.analysis_sets.get_supabase_client", return_value=mock_supabase), \
         patch("app.api.v1.analysis_sets.get_pl_data", return_value=[]), \
         patch("app.api.v1.analysis_sets.generate_analysis_ppt", return_value=b"fake_pptx"):
        response = builder_client.post("/api/v1/analysis-sets/SET_ID/export/ppt")
    assert response.status_code == 200
    assert "openxmlformats-officedocument.presentationml" in response.headers["content-type"]
    assert "attachment" in response.headers["content-disposition"]

def test_export_ppt_forbidden(builder_client):
    # owner_id != current user
    ...  # 403 체크

def test_export_ppt_not_found(builder_client):
    # 빈 DB mock
    ...  # 404 체크
```

### Frontend AnalysisSetItem 수정 위치

`AnalysisSetItem.tsx:50` — `<ShareDialog>` 옆에 PPT 버튼 추가:
```tsx
// canEdit 블록 내부, ShareDialog 뒤에 추가
{canEdit && (
  <>
    <ShareDialog setId={set.id} />
    <PptExportButton set={set} />  // 또는 인라인 처리
    <button onClick={() => onEdit(set)}>수정</button>
    <button onClick={...}>삭제</button>
  </>
)}
```

PPT export는 mutation이 있으므로 `AnalysisSetItem` 내부에 `useMutation` 직접 추가 권장 (Props로 콜백 넘길 필요 없음).

### 아키텍처 준수 사항

- **모든 API 호출은 `lib/api.ts` 경유** — `AnalysisSetItem`에서 직접 fetch 금지
- **Toast 규칙**: success 3초 자동 소멸, error 수동 닫기 (`duration: undefined`)
- **`isPending` 패턴**: mutation 진행 중 버튼 disabled + 로딩 인디케이터
- **소유권 체크 패턴**: `get_user_role(user.id)` + `existing["owner_id"] != user.id` (기존 delete/share와 동일)
- **파일명 규칙**: `{set_name}_{YYYY-MM-DD}.pptx` — 공백/특수문자 주의 (파일명 안전 변환 불필요시 그대로 사용)

### 이전 스토리에서 배운 패턴

**Story 5.1/5.2 에서 (가장 최근):**
- 테스트 auth mock: `app.dependency_overrides[get_current_user] = lambda: MOCK_USER`
- `_mock_supabase_with_...()` 헬퍼 패턴으로 테이블별 mock 분기
- `patch("app.api.v1.xxx.get_supabase_client", return_value=mock)`

**Story 4.1 공유 링크 (동일 analysis_sets.py 패턴):**
- `get_user_role(user.id)` — 역할 체크 함수 (`core/auth.py`)
- `existing["owner_id"] != user.id` 소유권 체크

**Story 1.6 차트 다운로드 (프론트 다운로드 패턴 참조):**
- 기존 구현을 확인하고 동일 패턴 적용

### Project Structure Notes

```
backend/
  requirements.txt          ← python-pptx>=1.0.0 추가
  app/
    api/v1/
      analysis_sets.py       ← export/ppt 엔드포인트 추가 (파일 하단)
    services/
      ppt_service.py         ← 신규: generate_analysis_ppt()
  tests/
    test_ppt_export.py       ← 신규: 3개 테스트

frontend/
  src/
    lib/
      api.ts                 ← apiGetBlob, exportAnalysisSetPpt 추가
    components/layout/
      AnalysisSetItem.tsx     ← PPT 버튼 + useMutation 추가
```

### References

- [Source: epics.md - Epic 6, Story 6.1] — AC 전체, BDD 시나리오, FR30
- [Source: architecture.md - API & Communication Patterns] — REST 패턴, 에러 응답 형식
- [Source: architecture.md - Deferred Decisions] — PPT Export 라이브러리 선택 (Phase 3) → python-pptx 채택
- [Source: backend/app/api/v1/analysis_sets.py:264-320] — share_analysis_set 소유권 체크 패턴 (동일 적용)
- [Source: backend/app/services/financial_service.py] — get_pl_data(corp_code, years) 재사용
- [Source: frontend/src/components/layout/AnalysisSetItem.tsx:32-70] — canEdit 조건 + 버튼 배치 패턴
- [Source: frontend/src/lib/api.ts] — apiPost, apiGet 패턴 → apiGetBlob 신규 추가
- [Source: architecture.md - Process Patterns] — isPending 버튼, toast 규칙

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- Content-Disposition 헤더에 한글 파일명 사용 시 UnicodeEncodeError 발생 → RFC 5987 `filename*=UTF-8''%EC%...` 형식으로 해결

### Completion Notes List

- Task 1: `python-pptx>=1.0.0` requirements.txt 추가 및 venv 설치 완료
- Task 2: `ppt_service.py` 구현 — Slide 1(제목), Slide 2~N(기업별 P&L 바차트), Slide N+1(비교 바차트). 재무 row dict 기반으로 처리 (FinancialStatement 객체 아닌 dict)
- Task 3: `POST /api/v1/analysis-sets/{set_id}/export/ppt` 엔드포인트 추가. 기존 share 패턴 동일한 소유권 체크. Content-Disposition에 RFC 5987 UTF-8 인코딩 적용
- Task 4: 테스트 4개 모두 통과 (200/403/404/Admin-200) — `generate_analysis_ppt` mock으로 python-pptx 직접 호출 없이 테스트
- Task 5: `apiPostBlob` (POST binary), `exportAnalysisSetPpt` 추가
- Task 6: PPT 버튼 `canEdit` 블록 내 ShareDialog 다음에 배치. `useMutation` + `Loader2` 스피너 + `isPending` disabled 적용
- Task 7: `npm run build` 성공, pytest 119 passed (기존 5 failed는 pre-existing, 회귀 없음)
- Code Review M1 fix: `document.body.appendChild(a)` / `removeChild(a)` 추가 — Firefox 크로스 브라우저 다운로드 호환성 보장
- Code Review M2 fix: Admin이 타인 소유 세트 내보내기 → 200 테스트 추가 (`test_export_ppt_admin_can_access_others_set`)
- Code Review M3 fix: `quote(filename.encode("utf-8"), safe="")` — '/' 문자 URL 인코딩 보장

### File List

- backend/requirements.txt
- backend/app/services/ppt_service.py (신규)
- backend/app/api/v1/analysis_sets.py
- backend/tests/test_ppt_export.py (신규)
- frontend/src/lib/api.ts
- frontend/src/components/layout/AnalysisSetItem.tsx
- _bmad-output/implementation-artifacts/sprint-status.yaml
