"""
API Gateway - 统一网关服务
负责路由、认证、限流、负载均衡
"""

from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx
import time
import logging
from typing import Optional

from backend.common.config import settings
from backend.common.auth import get_current_user
from backend.common.schemas import BaseResponse, ErrorResponse

# 配置日志
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=f"{settings.APP_NAME} - API Gateway",
    description="统一API网关服务",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置限流器
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# 信任主机中间件
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # 生产环境应限制具体域名
)


# ==================== 中间件 ====================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response


# ==================== 健康检查 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "api-gateway"}


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "EasyTune-LLM API Gateway",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


# ==================== 代理函数 ====================

async def proxy_request(
    request: Request,
    service_url: str,
    path: str,
    method: str = "GET"
) -> JSONResponse:
    """
    代理请求到后端微服务
    """
    # 构建目标URL
    target_url = f"{service_url}/{path}"
    
    # 获取请求头
    headers = dict(request.headers)
    headers.pop("host", None)  # 移除host头
    
    # 获取请求体
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params
            )
            
            return JSONResponse(
                content=response.json() if response.text else {},
                status_code=response.status_code,
                headers=dict(response.headers)
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Service timeout"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable"
        )
    except Exception as e:
        logger.error(f"Proxy error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal gateway error"
        )


# ==================== 认证路由 ====================

from backend.api_gateway.routers import auth, models, tasks, datasets, users

app.include_router(auth.router, prefix=f"{settings.API_PREFIX}/auth", tags=["认证"])
app.include_router(users.router, prefix=f"{settings.API_PREFIX}/users", tags=["用户管理"])
app.include_router(models.router, prefix=f"{settings.API_PREFIX}/models", tags=["模型管理"])
app.include_router(datasets.router, prefix=f"{settings.API_PREFIX}/datasets", tags=["数据集管理"])
app.include_router(tasks.router, prefix=f"{settings.API_PREFIX}/tasks", tags=["任务管理"])


# ==================== 错误处理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=str(exc.status_code)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.DEBUG else None
        ).dict()
    )


# ==================== 启动和关闭事件 ====================

@app.on_event("startup")
async def startup_event():
    """启动事件"""
    logger.info("API Gateway starting up...")
    logger.info(f"API Gateway running on {settings.HOST}:{settings.PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """关闭事件"""
    logger.info("API Gateway shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1
    )

