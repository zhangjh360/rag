"""
日志管理工具
提供日志查看、清理、归档等功能
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from app.config.logging_config import get_logging_config

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.config = get_logging_config()
    
    def get_log_files(self, log_type: str = None) -> List[Dict]:
        """
        获取日志文件列表
        
        Args:
            log_type (str, optional): 日志类型过滤
            
        Returns:
            List[Dict]: 日志文件信息列表
        """
        log_files = []
        
        if log_type:
            type_dirs = [self.log_dir / log_type]
        else:
            type_dirs = [d for d in self.log_dir.iterdir() if d.is_dir()]
        
        for type_dir in type_dirs:
            if not type_dir.exists():
                continue
                
            for log_file in type_dir.iterdir():
                if log_file.is_file() and log_file.suffix in ['.log', '.txt']:
                    stat = log_file.stat()
                    log_files.append({
                        "name": log_file.name,
                        "path": str(log_file),
                        "type": type_dir.name,
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / 1024 / 1024, 2),
                        "created": datetime.fromtimestamp(stat.st_ctime),
                        "modified": datetime.fromtimestamp(stat.st_mtime)
                    })
        
        # 按修改时间排序
        log_files.sort(key=lambda x: x["modified"], reverse=True)
        return log_files
    
    def read_log_file(self, file_path: str, lines: int = 100) -> List[str]:
        """
        读取日志文件内容
        
        Args:
            file_path (str): 日志文件路径
            lines (int): 读取的行数（从末尾开始）
            
        Returns:
            List[str]: 日志行列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if lines > 0 else all_lines
        except Exception as e:
            return [f"读取日志文件失败: {str(e)}"]
    
    def search_logs(self, 
                   query: str, 
                   log_type: str = None, 
                   hours: int = 24) -> List[Dict]:
        """
        搜索日志内容
        
        Args:
            query (str): 搜索关键词
            log_type (str, optional): 日志类型
            hours (int): 搜索最近几小时的日志
            
        Returns:
            List[Dict]: 匹配的日志条目
        """
        results = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        log_files = self.get_log_files(log_type)
        
        for log_file in log_files:
            if log_file["modified"] < cutoff_time:
                continue
                
            try:
                with open(log_file["path"], 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            results.append({
                                "file": log_file["name"],
                                "type": log_file["type"],
                                "line": line_num,
                                "content": line.strip(),
                                "timestamp": self._extract_timestamp(line)
                            })
            except Exception as e:
                continue
        
        return results
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """从日志行中提取时间戳"""
        try:
            # 假设日志格式为: 2024-01-01 12:00:00 - ...
            parts = line.split(" - ")
            if len(parts) > 0:
                return parts[0]
        except:
            pass
        return None
    
    def clean_old_logs(self, days: int = 30) -> Dict:
        """
        清理旧日志文件
        
        Args:
            days (int): 保留天数
            
        Returns:
            Dict: 清理结果统计
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_files = []
        total_size = 0
        
        log_files = self.get_log_files()
        
        for log_file in log_files:
            if log_file["modified"] < cutoff_date:
                try:
                    file_path = Path(log_file["path"])
                    total_size += log_file["size"]
                    file_path.unlink()
                    cleaned_files.append(log_file["name"])
                except Exception as e:
                    continue
        
        return {
            "cleaned_files": len(cleaned_files),
            "freed_space_mb": round(total_size / 1024 / 1024, 2),
            "files": cleaned_files
        }
    
    def archive_logs(self, days: int = 7) -> Dict:
        """
        归档日志文件
        
        Args:
            days (int): 归档多少天前的日志
            
        Returns:
            Dict: 归档结果统计
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        archived_files = []
        total_size = 0
        
        log_files = self.get_log_files()
        
        for log_file in log_files:
            if log_file["modified"] < cutoff_date:
                try:
                    source_path = Path(log_file["path"])
                    archive_dir = self.log_dir / "archive" / log_file["type"]
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 添加时间戳到文件名
                    timestamp = log_file["modified"].strftime("%Y%m%d_%H%M%S")
                    archive_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
                    archive_path = archive_dir / archive_name
                    
                    shutil.move(str(source_path), str(archive_path))
                    total_size += log_file["size"]
                    archived_files.append(archive_name)
                except Exception as e:
                    continue
        
        return {
            "archived_files": len(archived_files),
            "archived_size_mb": round(total_size / 1024 / 1024, 2),
            "files": archived_files
        }
    
    def get_log_statistics(self) -> Dict:
        """
        获取日志统计信息
        
        Returns:
            Dict: 日志统计信息
        """
        log_files = self.get_log_files()
        
        stats = {
            "total_files": len(log_files),
            "total_size_mb": 0,
            "by_type": {},
            "oldest_file": None,
            "newest_file": None
        }
        
        if not log_files:
            return stats
        
        for log_file in log_files:
            # 总大小
            stats["total_size_mb"] += log_file["size_mb"]
            
            # 按类型统计
            log_type = log_file["type"]
            if log_type not in stats["by_type"]:
                stats["by_type"][log_type] = {
                    "count": 0,
                    "size_mb": 0
                }
            stats["by_type"][log_type]["count"] += 1
            stats["by_type"][log_type]["size_mb"] += log_file["size_mb"]
            
            # 最旧和最新文件
            if stats["oldest_file"] is None or log_file["modified"] < stats["oldest_file"]["modified"]:
                stats["oldest_file"] = log_file
            
            if stats["newest_file"] is None or log_file["modified"] > stats["newest_file"]["modified"]:
                stats["newest_file"] = log_file
        
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        
        for log_type in stats["by_type"]:
            stats["by_type"][log_type]["size_mb"] = round(
                stats["by_type"][log_type]["size_mb"], 2
            )
        
        return stats
    
    def export_logs(self, 
                   output_file: str, 
                   log_type: str = None, 
                   hours: int = 24) -> bool:
        """
        导出日志到文件
        
        Args:
            output_file (str): 输出文件路径
            log_type (str, optional): 日志类型
            hours (int): 导出最近几小时的日志
            
        Returns:
            bool: 是否成功
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            log_files = self.get_log_files(log_type)
            
            with open(output_file, 'w', encoding='utf-8') as out_f:
                out_f.write(f"# 日志导出 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                out_f.write(f"# 导出范围: 最近 {hours} 小时\n")
                out_f.write(f"# 日志类型: {log_type or '全部'}\n\n")
                
                for log_file in log_files:
                    if log_file["modified"] < cutoff_time:
                        continue
                    
                    out_f.write(f"\n## {log_file['name']} ({log_file['type']})\n")
                    out_f.write(f"# 文件大小: {log_file['size_mb']} MB\n")
                    out_f.write(f"# 修改时间: {log_file['modified']}\n\n")
                    
                    try:
                        with open(log_file["path"], 'r', encoding='utf-8') as in_f:
                            for line in in_f:
                                out_f.write(line)
                    except Exception as e:
                        out_f.write(f"# 读取文件失败: {str(e)}\n")
            
            return True
            
        except Exception as e:
            return False

# 全局日志管理器实例
log_manager = LogManager()
