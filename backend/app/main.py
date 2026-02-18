"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import transition, physical, scenarios, esg, company

app = FastAPI(
    title="Climate Risk Platform API",
    description="기후 리스크 분석 플랫폼 - 전환 리스크, 물리적 리스크, ESG 공시",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scenarios.router, prefix="/api/v1", tags=["scenarios"])
app.include_router(company.router, prefix="/api/v1", tags=["company"])
app.include_router(transition.router, prefix="/api/v1/transition-risk", tags=["transition-risk"])
app.include_router(physical.router, prefix="/api/v1/physical-risk", tags=["physical-risk"])
app.include_router(esg.router, prefix="/api/v1/esg", tags=["esg"])


@app.get("/")
def root():
    return {"message": "Climate Risk Platform API v1.0", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
