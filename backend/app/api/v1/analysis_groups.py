"""
분석 그룹 API — 분석 세트를 묶는 폴더
POST   /api/v1/analysis-groups          : 그룹 생성
GET    /api/v1/analysis-groups          : 그룹 목록 조회
PATCH  /api/v1/analysis-groups/{id}     : 그룹 수정 (이름/순서)
DELETE /api/v1/analysis-groups/{id}     : 그룹 삭제 (세트는 미분류로)
"""
from fastapi import APIRouter, HTTPException, Response, status
from app.core.database import get_supabase_client
from app.models.schemas import AnalysisGroup, AnalysisGroupCreate, AnalysisGroupUpdate

router = APIRouter()


@router.post("/analysis-groups", status_code=status.HTTP_201_CREATED, response_model=AnalysisGroup)
async def create_analysis_group(body: AnalysisGroupCreate):
    supabase = get_supabase_client()
    try:
        res = supabase.table("analysis_groups").insert({
            "name": body.name,
            "display_order": 0,
        }).execute()
    except Exception:
        raise HTTPException(503, detail={"error": "DB_UNAVAILABLE", "message": "DB 오류", "status_code": 503})
    return res.data[0]


@router.get("/analysis-groups", response_model=list[AnalysisGroup])
async def list_analysis_groups():
    supabase = get_supabase_client()
    try:
        res = supabase.table("analysis_groups").select("*").order("display_order").order("created_at").execute()
    except Exception:
        raise HTTPException(503, detail={"error": "DB_UNAVAILABLE", "message": "DB 오류", "status_code": 503})
    return res.data


@router.patch("/analysis-groups/{group_id}", response_model=AnalysisGroup)
async def update_analysis_group(group_id: str, body: AnalysisGroupUpdate):
    supabase = get_supabase_client()
    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.display_order is not None:
        update_data["display_order"] = body.display_order
    if not update_data:
        raise HTTPException(400, detail={"error": "NO_DATA", "message": "변경 항목 없음", "status_code": 400})
    try:
        res = supabase.table("analysis_groups").update(update_data).eq("id", group_id).execute()
    except Exception:
        raise HTTPException(503, detail={"error": "DB_UNAVAILABLE", "message": "DB 오류", "status_code": 503})
    if not res.data:
        raise HTTPException(404, detail={"error": "NOT_FOUND", "message": "그룹을 찾을 수 없습니다.", "status_code": 404})
    return res.data[0]


@router.delete("/analysis-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis_group(group_id: str):
    supabase = get_supabase_client()
    # 세트의 group_id를 null로 (ON DELETE SET NULL이 처리하지만 명시적으로도)
    try:
        supabase.table("analysis_sets").update({"group_id": None}).eq("group_id", group_id).execute()
        supabase.table("analysis_groups").delete().eq("id", group_id).execute()
    except Exception:
        raise HTTPException(503, detail={"error": "DB_UNAVAILABLE", "message": "DB 오류", "status_code": 503})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
