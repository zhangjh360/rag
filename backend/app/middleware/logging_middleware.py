"""
日志中间件
记录HTTP请求和响应信息
"""

import time
import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config.logging_config import get_access_logger, get_error_logger
import logging

logger = get_access_logger()
error_logger = get_error_logger()

class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTP请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next):
        """处理HTTP请求并记录日志"""
        start_time = time.time()
        
        # 获取请求信息
        client_ip = self._get_client_ip(request)
        method = request.method
        url = str(request.url)
        path = request.url.path
        query_params = str(request.query_params)
        user_agent = request.headers.get("user-agent", "")
        
        # 记录请求开始
        request_id = self._generate_request_id()
        logger.info(
            f"[{request_id}] 请求开始 - {method} {path} "
            f"来自 {client_ip} - User-Agent: {user_agent}"
        )
        
        if query_params:
            logger.debug(f"[{request_id}] 查询参数: {query_params}")
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            status_code = response.status_code
            response_size = self._get_response_size(response)
            
            logger.info(
                f"[{request_id}] 请求完成 - {method} {path} "
                f"状态码: {status_code} 处理时间: {process_time:.3f}s "
                f"响应大小: {response_size} bytes"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 记录错误
            process_time = time.time() - start_time
            error_logger.error(
                f"[{request_id}] 请求失败 - {method} {path} "
                f"错误: {str(e)} 处理时间: {process_time:.3f}s",
                exc_info=True
            )
            
            # 重新抛出异常
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # 直接连接
        if hasattr(request.client, "host"):
            return request.client.host
        
        return "unknown"
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_response_size(self, response: Response) -> int:
        """获取响应大小"""
        try:
            if hasattr(response, "body"):
                return len(response.body)
            return 0
        except:
            return 0

class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """错误日志中间件"""

    async def dispatch(self, request: Request, call_next):
        """处理请求并记录错误"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # 记录详细错误信息
            error_info = {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": str(request.query_params),
                "headers": dict(request.headers),
                "client_ip": self._get_client_ip(request),
                "error": str(e),
                "error_type": type(e).__name__
            }

            error_logger.error(
                f"HTTP错误 - {request.method} {request.url.path}",
                extra={"error_info": error_info},
                exc_info=True
            )

            raise

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 直接连接
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """性能日志中间件"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next):
        """记录性能信息"""
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录慢请求
        if process_time > self.slow_request_threshold:
            logger.warning(
                f"慢请求检测 - {request.method} {request.url.path} "
                f"处理时间: {process_time:.3f}s (阈值: {self.slow_request_threshold}s)"
            )
        
        return response
