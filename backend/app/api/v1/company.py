"""Company / facility endpoints."""

from fastapi import APIRouter, HTTPException

from ...data.sample_facilities import get_all_facilities, get_facility_by_id, get_facilities_by_sector

router = APIRouter()


@router.get("/company/facilities")
def list_facilities(sector: str | None = None):
    if sector:
        return get_facilities_by_sector(sector)
    return get_all_facilities()


@router.get("/company/facilities/{facility_id}")
def get_facility(facility_id: str):
    f = get_facility_by_id(facility_id)
    if not f:
        raise HTTPException(404, "Facility not found")
    return f


@router.get("/company/sectors")
def list_sectors():
    facs = get_all_facilities()
    sectors = sorted(set(f["sector"] for f in facs))
    return sectors
