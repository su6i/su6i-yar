import logging
import sys
import os
from logging.handlers import RotatingFileHandler

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and clean output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        # Shorten format for cleaner output
        log_fmt = "%(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name="SushiYar", level=logging.INFO):
    """Configure and return a logger instance."""
    logger = logging.getLogger(name)
    logger.propagate = False
    
    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    
    # --- File Handler (Add with robustness) ---
    try:
        # We look for LOGS_DIR but avoid circular import from .config
        data_dir = os.path.expanduser("~/.su6i-yar")
        logs_dir = os.path.join(data_dir, "logs")
        
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
            
        log_file = os.path.join(logs_dir, "bot.log")
        
        # Rotating: Max 5MB per file, keep last 5 backups
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
        )
        file_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to console only if file logging fails (e.g. permissions)
        print(f"⚠️ Failed to setup file logging: {e}", file=sys.stderr)

    logger.setLevel(level)
    
    # Suppress verbose logs from third-party libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    
    return logger

# Default logger instance
logger = setup_logger()
