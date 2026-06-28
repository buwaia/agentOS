from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from src.handlers import create_job, list_jobs, get_job, advance, approve, get_artifact

app = FastAPI(title="Math Solver Delivery Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_job.router)
app.include_router(list_jobs.router)
app.include_router(get_job.router)
app.include_router(advance.router)
app.include_router(approve.router)
app.include_router(get_artifact.router)

handler = Mangum(app)
