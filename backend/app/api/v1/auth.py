from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register() -> dict[str, str]:
    # TODO P3.4 — register with hashed password
    return {"status": "not_implemented"}


@router.post("/login")
async def login() -> dict[str, str]:
    # TODO P3.4 — issue JWT + refresh token
    return {"status": "not_implemented"}


@router.post("/refresh")
async def refresh() -> dict[str, str]:
    # TODO P3.4 — rotate refresh token, issue new access token
    return {"status": "not_implemented"}
