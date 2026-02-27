import logging
import sys

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
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter())
    logger.addHandler(console_handler)
    logger.setLevel(level)
    
    # Suppress verbose logs from third-party libs
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google_genai").setLevel(logging.WARNING)
    
    return logger

# Default logger instance
logger = setup_logger()
