"""
日志管理API接口
提供日志查看、搜索、清理等功能
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
from app.utils.log_manager import log_manager
from app.config.logging_config import get_app_logger
from pydantic import BaseModel

router = APIRouter()
logger = get_app_logger()

class LogFileInfo(BaseModel):
    """日志文件信息模型"""
    name: str
    path: str
    type: str
    size: int
    size_mb: float
    created: str
    modified: str

class LogSearchResult(BaseModel):
    """日志搜索结果模型"""
    file: str
    type: str
    line: int
    content: str
    timestamp: Optional[str] = None

class LogStatistics(BaseModel):
    """日志统计信息模型"""
    total_files: int
    total_size_mb: float
    by_type: dict
    oldest_file: Optional[LogFileInfo] = None
    newest_file: Optional[LogFileInfo] = None

class CleanResult(BaseModel):
    """清理结果模型"""
    cleaned_files: int
    freed_space_mb: float
    files: List[str]

@router.get("/logs/files", response_model=List[LogFileInfo])
async def get_log_files(
    log_type: Optional[str] = Query(None, description="日志类型过滤")
):
    """获取日志文件列表"""
    try:
        log_files = log_manager.get_log_files(log_type)
        return [
            LogFileInfo(
                name=file["name"],
                path=file["path"],
                type=file["type"],
                size=file["size"],
                size_mb=file["size_mb"],
                created=file["created"].isoformat(),
                modified=file["modified"].isoformat()
            )
            for file in log_files
        ]
    except Exception as e:
        logger.error(f"获取日志文件列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志文件列表失败: {str(e)}")

@router.get("/logs/read/{file_path:path}")
async def read_log_file(
    file_path: str,
    lines: int = Query(100, description="读取行数，0表示全部")
):
    """读取日志文件内容"""
    try:
        content = log_manager.read_log_file(file_path, lines)
        return {
            "file_path": file_path,
            "lines_count": len(content),
            "content": content
        }
    except Exception as e:
        logger.error(f"读取日志文件失败: {e}")
        raise HTTPException(status_code=500, detail=f"读取日志文件失败: {str(e)}")

@router.get("/logs/search", response_model=List[LogSearchResult])
async def search_logs(
    query: str = Query(..., description="搜索关键词"),
    log_type: Optional[str] = Query(None, description="日志类型"),
    hours: int = Query(24, description="搜索最近几小时的日志")
):
    """搜索日志内容"""
    try:
        results = log_manager.search_logs(query, log_type, hours)
        return [
            LogSearchResult(
                file=result["file"],
                type=result["type"],
                line=result["line"],
                content=result["content"],
                timestamp=result["timestamp"]
            )
            for result in results
        ]
    except Exception as e:
        logger.error(f"搜索日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索日志失败: {str(e)}")

@router.get("/logs/statistics", response_model=LogStatistics)
async def get_log_statistics():
    """获取日志统计信息"""
    try:
        stats = log_manager.get_log_statistics()
        return LogStatistics(
            total_files=stats["total_files"],
            total_size_mb=stats["total_size_mb"],
            by_type=stats["by_type"],
            oldest_file=LogFileInfo(
                name=stats["oldest_file"]["name"],
                path=stats["oldest_file"]["path"],
                type=stats["oldest_file"]["type"],
                size=stats["oldest_file"]["size"],
                size_mb=stats["oldest_file"]["size_mb"],
                created=stats["oldest_file"]["created"].isoformat(),
                modified=stats["oldest_file"]["modified"].isoformat()
            ) if stats["oldest_file"] else None,
            newest_file=LogFileInfo(
                name=stats["newest_file"]["name"],
                path=stats["newest_file"]["path"],
                type=stats["newest_file"]["type"],
                size=stats["newest_file"]["size"],
                size_mb=stats["newest_file"]["size_mb"],
                created=stats["newest_file"]["created"].isoformat(),
                modified=stats["newest_file"]["modified"].isoformat()
            ) if stats["newest_file"] else None
        )
    except Exception as e:
        logger.error(f"获取日志统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志统计失败: {str(e)}")

@router.post("/logs/clean", response_model=CleanResult)
async def clean_old_logs(
    days: int = Query(30, description="保留天数")
):
    """清理旧日志文件"""
    try:
        result = log_manager.clean_old_logs(days)
        logger.info(f"清理了 {result['cleaned_files']} 个旧日志文件，释放了 {result['freed_space_mb']} MB 空间")
        return CleanResult(
            cleaned_files=result["cleaned_files"],
            freed_space_mb=result["freed_space_mb"],
            files=result["files"]
        )
    except Exception as e:
        logger.error(f"清理日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理日志失败: {str(e)}")

@router.post("/logs/archive", response_model=CleanResult)
async def archive_logs(
    days: int = Query(7, description="归档多少天前的日志")
):
    """归档日志文件"""
    try:
        result = log_manager.archive_logs(days)
        logger.info(f"归档了 {result['archived_files']} 个日志文件，大小 {result['archived_size_mb']} MB")
        return CleanResult(
            cleaned_files=result["archived_files"],
            freed_space_mb=result["archived_size_mb"],
            files=result["files"]
        )
    except Exception as e:
        logger.error(f"归档日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"归档日志失败: {str(e)}")

@router.post("/logs/export")
async def export_logs(
    output_file: str = Query(..., description="输出文件路径"),
    log_type: Optional[str] = Query(None, description="日志类型"),
    hours: int = Query(24, description="导出最近几小时的日志")
):
    """导出日志到文件"""
    try:
        success = log_manager.export_logs(output_file, log_type, hours)
        if success:
            return {"message": f"日志已导出到 {output_file}"}
        else:
            raise HTTPException(status_code=500, detail="导出日志失败")
    except Exception as e:
        logger.error(f"导出日志失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出日志失败: {str(e)}")

@router.get("/logs/directories")
async def get_log_directories():
    """获取日志目录结构"""
    try:
        from pathlib import Path
        log_dir = Path("logs")
        
        def get_directory_tree(path: Path, prefix: str = ""):
            tree = []
            if path.is_dir():
                for item in sorted(path.iterdir()):
                    if item.is_dir():
                        tree.append({
                            "name": item.name,
                            "type": "directory",
                            "path": str(item),
                            "children": get_directory_tree(item, prefix + "  ")
                        })
                    else:
                        tree.append({
                            "name": item.name,
                            "type": "file",
                            "path": str(item),
                            "size": item.stat().st_size if item.exists() else 0
                        })
            return tree
        
        return {
            "log_directory": str(log_dir),
            "exists": log_dir.exists(),
            "tree": get_directory_tree(log_dir) if log_dir.exists() else []
        }
    except Exception as e:
        logger.error(f"获取日志目录结构失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取日志目录结构失败: {str(e)}")
