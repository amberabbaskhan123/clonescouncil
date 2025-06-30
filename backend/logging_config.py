#!/usr/bin/env python3
"""
Centralized Logging Configuration
Provides consistent logging setup across all backend services
"""

import logging
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    enable_console: bool = True


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Setup centralized logging configuration."""
    if config is None:
        # Create config from environment variables
        config = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE"),
            enable_console=os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true"
        )
    
    # Convert string level to logging level
    level = getattr(logging, config.level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(config.format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler if enabled
    if config.enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if file path is specified
    if config.file_path:
        try:
            file_handler = logging.FileHandler(config.file_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to console if file logging fails
            print(f"Warning: Could not setup file logging to {config.file_path}: {e}")
            if not config.enable_console:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(level)
                console_handler.setFormatter(formatter)
                root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)


# Setup logging on module import
setup_logging() 