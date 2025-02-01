import os
import logging
import colorlog

def setup_logging(name: str) -> logging.Logger:
    """
    Setup logging configuration with consistent format and colors across the application.
    
    Args:
        name: The name of the logger, typically __name__
        
    Returns:
        A configured logger instance
    """
    # Create color formatter
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s[%(asctime)s][%(name)s] %(message)s",
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
        secondary_log_colors={},
        style='%'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Remove any existing handlers
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
    
    # Return the named logger
    return logging.getLogger(name) 