"""
AI 요약 서비스 — Story 6.2
분석 세트의 재무 데이터를 LLM으로 요약하고 자연어 질의에 답변
[Source: architecture.md - Service Layer Patterns]
"""
import os
from typing import Optional

import google.generativeai as genai

# 모듈 레벨 지연 싱글턴 — 요청마다 재생성 방지
_model: Optional[genai.GenerativeModel] = None


class LLMAIError(Exception):
    """LLM API 호출 실패 시 발생"""


def _get_model() -> genai.GenerativeModel:
    """Gemini 모델 지연 싱글턴 반환.

    Raises:
        LLMAIError: GOOGLE_API_KEY 미설정 시
    """
    global _model
    if _model is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise LLMAIError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다")
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-1.5-flash")
    return _model


def generate_financial_summary(
    set_name: str,
    company_codes: list[str],
    financials_by_corp: dict,
) -> str:
    """분석 세트 재무 트렌드 자연어 요약 생성.

    Args:
        set_name: 분석 세트 이름
        company_codes: 기업 코드 목록
        financials_by_corp: {corp_code: [재무 데이터 row dict, ...]} 형태

    Returns:
        LLM이 생성한 한국어 요약 텍스트

    Raises:
        LLMAIError: LLM API 호출 실패 시
    """
    context = _build_financial_context(set_name, company_codes, financials_by_corp)
    system_prompt = (
        "당신은 재무 분석 전문가입니다. "
        "아래 재무 데이터를 바탕으로 핵심 트렌드(매출 성장률, 영업이익률 변화, 주요 인사이트)를 "
        "3-5문단으로 한국어로 요약하세요. 수치는 억원 단위로 표현하세요."
    )
    return _call_llm(system_prompt, context, max_tokens=1024)


def answer_financial_question(
    question: str,
    set_name: str,
    company_codes: list[str],
    financials_by_corp: dict,
) -> str:
    """재무 데이터 컨텍스트 기반 자연어 질의 답변 생성.

    Args:
        question: 사용자 질의 텍스트
        set_name: 분석 세트 이름
        company_codes: 기업 코드 목록
        financials_by_corp: {corp_code: [재무 데이터 row dict, ...]} 형태

    Returns:
        LLM이 생성한 한국어 답변 텍스트

    Raises:
        LLMAIError: LLM API 호출 실패 시
    """
    context = _build_financial_context(set_name, company_codes, financials_by_corp)
    system_prompt = (
        "당신은 재무 분석 전문가입니다. "
        "아래 재무 데이터를 참고하여 사용자의 질문에 한국어로 답변하세요. "
        "수치는 억원 단위로 표현하세요."
    )
    user_message = f"{context}\n\n질문: {question}"
    return _call_llm(system_prompt, user_message, max_tokens=1500)


def _build_financial_context(
    set_name: str,
    company_codes: list[str],
    financials_by_corp: dict,
) -> str:
    """재무 데이터를 LLM 프롬프트용 텍스트로 변환 (억 단위).

    Args:
        set_name: 분석 세트 이름
        company_codes: 기업 코드 목록
        financials_by_corp: {corp_code: [재무 데이터 row dict, ...]} 형태

    Returns:
        구조화된 재무 데이터 텍스트
    """
    lines = [
        f"분석 세트: {set_name}",
        f"포함 기업: {', '.join(company_codes)}",
        "",
    ]

    for corp_code in company_codes:
        data = financials_by_corp.get(corp_code, [])
        by_year: dict = {}
        for row in data:
            year = row["bsns_year"]
            account_key = row["account_key"]
            amount = (row.get("amount") or 0) / 100_000_000
            by_year.setdefault(year, {})[account_key] = round(amount, 1)

        lines.append(f"[{corp_code} P&L (억원)]")
        if not by_year:
            lines.append("  데이터 없음")
        else:
            for year in sorted(by_year.keys()):
                yr = by_year[year]
                revenue = yr.get("revenue", 0)
                op_profit = yr.get("operating_profit", 0)
                net_income = yr.get("net_income", 0)
                lines.append(
                    f"  {year}: 매출={revenue}, 영업이익={op_profit}, 순이익={net_income}"
                )
        lines.append("")

    return "\n".join(lines)


def _call_llm(system_prompt: str, user_message: str, max_tokens: int) -> str:
    """Google Gemini API 호출.

    Args:
        system_prompt: 시스템 프롬프트
        user_message: 사용자 메시지
        max_tokens: 최대 토큰 수

    Returns:
        LLM 응답 텍스트

    Raises:
        LLMAIError: API 호출 실패 시
    """
    try:
        model = _get_model()
        response = model.generate_content(
            f"{system_prompt}\n\n{user_message}",
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
            ),
        )
        return response.text
    except Exception as e:
        raise LLMAIError(f"LLM API 호출 실패: {e}") from e
