from fastapi import APIRouter

router = APIRouter()


@router.post("")
async def create_trip() -> dict[str, str]:
    # TODO P3.2 — full SSE streaming implementation
    return {"status": "not_implemented"}


@router.get("/{trip_id}/stream")
async def stream_trip(trip_id: str) -> dict[str, str]:
    # TODO P3.2 — SSE event stream
    return {"status": "not_implemented", "trip_id": trip_id}
