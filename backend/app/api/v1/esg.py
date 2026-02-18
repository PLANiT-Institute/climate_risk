"""ESG disclosure endpoints."""

from fastapi import APIRouter, HTTPException, Query

from ...services.esg_compliance import assess_framework, get_disclosure_data

router = APIRouter()

VALID_FRAMEWORKS = ("issb", "tcfd", "kssb")


def _validate(fw: str) -> None:
    if fw not in VALID_FRAMEWORKS:
        raise HTTPException(400, f"Unknown framework: {fw}. Valid: {list(VALID_FRAMEWORKS)}")


@router.get("/assessment")
def esg_assessment(framework: str = Query("tcfd")):
    _validate(framework)
    return assess_framework(framework)


@router.get("/disclosure-data")
def esg_disclosure_data(framework: str = Query("tcfd")):
    _validate(framework)
    return get_disclosure_data(framework)


@router.get("/frameworks")
def list_frameworks():
    return [
        {"id": "issb", "name": "ISSB (IFRS S2)", "description": "국제지속가능성기준위원회 기후 공시"},
        {"id": "tcfd", "name": "TCFD", "description": "기후변화 관련 재무정보 공개 태스크포스"},
        {"id": "kssb", "name": "KSSB", "description": "한국 지속가능성 기준위원회"},
    ]
