import os
import logging

def setup_logging(name: str) -> logging.Logger:
    """
    Setup logging configuration with consistent format across the application.
    
    Args:
        name: The name of the logger, typically __name__
        
    Returns:
        A configured logger instance
    """
    logging.basicConfig(
        level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name) 