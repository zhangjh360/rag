"""
日志配置模块
提供统一的日志配置和管理功能
"""

import os
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

class LoggingConfig:
    """日志配置类"""
    
    def __init__(self, 
                 log_dir: str = "logs",
                 log_level: str = "INFO",
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 enable_console: bool = True,
                 enable_file: bool = True):
        """
        初始化日志配置
        
        Args:
            log_dir (str): 日志文件存储目录
            log_level (str): 日志级别
            max_file_size (int): 单个日志文件最大大小（字节）
            backup_count (int): 保留的备份文件数量
            enable_console (bool): 是否启用控制台输出
            enable_file (bool): 是否启用文件输出
        """
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        
        # 创建日志目录
        self._create_log_directories()
    
    def _create_log_directories(self):
        """创建日志目录结构"""
        directories = [
            self.log_dir,
            self.log_dir / "app",      # 应用日志
            self.log_dir / "error",    # 错误日志
            self.log_dir / "access",   # 访问日志
            self.log_dir / "debug",    # 调试日志
            self.log_dir / "archive"   # 归档日志
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_formatter(self, include_time: bool = True) -> logging.Formatter:
        """
        获取日志格式化器
        
        Args:
            include_time (bool): 是否包含时间戳
            
        Returns:
            logging.Formatter: 格式化器
        """
        if include_time:
            format_string = (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        else:
            format_string = (
                "%(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        
        return logging.Formatter(
            format_string,
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def setup_logger(self, 
                    name: str,
                    log_file: Optional[str] = None,
                    level: Optional[int] = None) -> logging.Logger:
        """
        设置指定名称的日志器
        
        Args:
            name (str): 日志器名称
            log_file (str, optional): 日志文件名
            level (int, optional): 日志级别
            
        Returns:
            logging.Logger: 配置好的日志器
        """
        logger = logging.getLogger(name)
        logger.setLevel(level or self.log_level)
        
        # 清除现有的处理器
        logger.handlers.clear()
        
        # 添加控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(self.get_formatter())
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if self.enable_file and log_file:
            file_path = self.log_dir / log_file
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=self.max_file_size,
                backupCount=self.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self.get_formatter())
            logger.addHandler(file_handler)
        
        return logger
    
    def setup_application_logging(self):
        """设置应用程序的日志配置"""
        # 根日志器配置
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 应用日志器
        app_logger = self.setup_logger(
            "app",
            "app/app.log"
        )
        
        # 错误日志器
        error_logger = self.setup_logger(
            "error",
            "error/error.log",
            level=logging.ERROR
        )
        
        # 访问日志器
        access_logger = self.setup_logger(
            "access",
            "access/access.log"
        )
        
        # 调试日志器
        debug_logger = self.setup_logger(
            "debug",
            "debug/debug.log",
            level=logging.DEBUG
        )
        
        # 设置第三方库的日志级别
        self._configure_third_party_loggers()
        
        return {
            "app": app_logger,
            "error": error_logger,
            "access": access_logger,
            "debug": debug_logger
        }
    
    def _configure_third_party_loggers(self):
        """配置第三方库的日志级别"""
        # 设置第三方库的日志级别
        third_party_loggers = {
            "uvicorn": logging.INFO,
            "uvicorn.access": logging.INFO,
            "uvicorn.error": logging.INFO,
            "fastapi": logging.INFO,
            "sqlalchemy": logging.WARNING,
            "sqlalchemy.engine": logging.WARNING,
            "openai": logging.WARNING,
            "transformers": logging.WARNING,
            "torch": logging.WARNING,
            "httpx": logging.WARNING,
        }
        
        for logger_name, level in third_party_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    
    def get_log_file_path(self, log_type: str, filename: str = None) -> Path:
        """
        获取日志文件路径
        
        Args:
            log_type (str): 日志类型 (app, error, access, debug)
            filename (str, optional): 自定义文件名
            
        Returns:
            Path: 日志文件路径
        """
        if filename:
            return self.log_dir / log_type / filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d")
            return self.log_dir / log_type / f"{log_type}_{timestamp}.log"
    
    def archive_old_logs(self, days: int = 30):
        """
        归档旧日志文件
        
        Args:
            days (int): 保留天数
        """
        import shutil
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        archive_dir = self.log_dir / "archive"
        
        for log_type_dir in self.log_dir.iterdir():
            if log_type_dir.is_dir() and log_type_dir.name != "archive":
                for log_file in log_type_dir.iterdir():
                    if log_file.is_file():
                        file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                        if file_time < cutoff_date:
                            # 移动到归档目录
                            archive_subdir = archive_dir / log_type_dir.name
                            archive_subdir.mkdir(exist_ok=True)
                            shutil.move(str(log_file), str(archive_subdir / log_file.name))

# 全局日志配置实例
def get_logging_config() -> LoggingConfig:
    """获取全局日志配置实例"""
    return LoggingConfig(
        log_dir=os.getenv("LOG_DIR", "logs"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_file_size=int(os.getenv("LOG_MAX_SIZE", "10485760")),  # 10MB
        backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
        enable_console=os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true",
        enable_file=os.getenv("LOG_ENABLE_FILE", "true").lower() == "true"
    )

# 便捷函数
def setup_logging():
    """设置应用程序日志"""
    config = get_logging_config()
    return config.setup_application_logging()

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)

def get_app_logger() -> logging.Logger:
    """获取应用日志器"""
    return logging.getLogger("app")

def get_error_logger() -> logging.Logger:
    """获取错误日志器"""
    return logging.getLogger("error")

def get_access_logger() -> logging.Logger:
    """获取访问日志器"""
    return logging.getLogger("access")

def get_debug_logger() -> logging.Logger:
    """获取调试日志器"""
    return logging.getLogger("debug")
