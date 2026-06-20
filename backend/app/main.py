import time
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, check_db_connection, SessionLocal
from app.routers import auth, ai, upload, payments, user, feedback, contact, growth, settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("examai-hub")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=== STARTUP: Initializing ExamAI Hub ===")

    try:
        init_db()
        logger.info("STARTUP: Database initialized")
    except Exception as e:
        logger.error(f"STARTUP FAILED: Database - {e}")
        raise

    if ADMIN_EMAIL and ADMIN_PASSWORD:
        from app.models import User
        from app.services.auth_service import hash_password
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
            if not admin:
                admin = User(
                    email=ADMIN_EMAIL,
                    username="admin",
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    full_name="Super Admin",
                    is_premium=True,
                    is_admin=True,
                )
                db.add(admin)
                db.commit()
                logger.info(f"STARTUP: Admin user created ({ADMIN_EMAIL})")
            else:
                if not admin.is_admin:
                    admin.is_admin = True
                if not admin.is_premium:
                    admin.is_premium = True
                db.commit()
                logger.info(f"STARTUP: Admin user verified ({ADMIN_EMAIL})")
        except Exception as e:
            logger.error(f"STARTUP: Admin check failed - {e}")
        finally:
            db.close()
    else:
        logger.info("STARTUP: No admin credentials configured")

    logger.info("=== STARTUP: ExamAI Hub Ready ===")
    yield


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://examaihub.com",
        "https://www.examaihub.com",
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.2f}s)")
    return response


@app.middleware("http")
async def cors_errors_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
            headers={
                "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                "Access-Control-Allow-Credentials": "true",
            },
        )


app.include_router(auth.router)
app.include_router(ai.router)
app.include_router(upload.router)
app.include_router(payments.router)
app.include_router(user.router)
app.include_router(feedback.router)
app.include_router(contact.router)
app.include_router(growth.router)
app.include_router(settings.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "healthy",
        "docs": "/docs",
        "environment": "production" if settings.is_production else "development",
    }


@app.get("/health", tags=["Health"])
def health():
    import uuid
    checks = {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}

    try:
        db_ok = check_db_connection()
        checks["database"] = "connected" if db_ok else "disconnected"
        if not db_ok:
            checks["status"] = "degraded"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        checks["status"] = "degraded"

    checks["payments"] = "configured" if settings.PAYPAL_CLIENT_ID else "demo_mode"
    checks["authentication"] = "active"
    checks["ai"] = "active"
    checks["storage"] = "active"
    checks["uptime_seconds"] = round(time.time() - START_TIME, 0) if START_TIME else 0
    checks["request_id"] = str(uuid.uuid4())[:8]

    return checks


START_TIME = time.time()

app.state.start_time = START_TIME


@app.get("/admin/stats", tags=["Admin"])
def admin_stats():
    from app.database import SessionLocal
    from app.models import User, Payment, Activity, Feedback
    from sqlalchemy import func
    db = SessionLocal()
    try:
        users = db.query(func.count(User.id)).scalar() or 0
        payments_count = db.query(func.count(Payment.id)).scalar() or 0
        activities = db.query(func.count(Activity.id)).scalar() or 0
        feedback_count = db.query(func.count(Feedback.id)).scalar() or 0
        premium_users = db.query(func.count(User.id)).filter(User.is_premium == True).scalar() or 0
        return {
            "total_users": users,
            "premium_users": premium_users,
            "total_payments": payments_count,
            "total_activities": activities,
            "total_feedback": feedback_count,
            "database": "connected" if check_db_connection() else "error",
            "uptime_seconds": round(time.time() - START_TIME, 0),
        }
    finally:
        db.close()
