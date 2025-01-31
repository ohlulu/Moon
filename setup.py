import os
import sys
import logging
from pathlib import Path
from setuptools import setup, find_packages
from src.utils.logging import setup_logging

# Check Python version
if sys.version_info < (3, 8):
    sys.exit('Python >= 3.8 is required')

# Setup logging
logger = setup_logging(__name__)

def create_directory_structure():
    """Create the project directory structure."""
    directories = [
        'src/collection',
        'src/database/models',
        'src/database/repositories',
        'src/indicators',
        'src/strategies',
        'src/config',
        'src/utils',
        'scripts',
        'docs/api',
        'docs/database',
        'docs/deployment',
        'reports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f'Created directory: {directory}')

def create_env_file():
    """Create .env file with template values."""
    if not os.path.exists('.env'):
        env_template = """# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=moon_crypto

# API Keys
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key

# Twitter API Configuration
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret

# News API Configuration
NEWS_API_KEY=your_news_api_key

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
"""
        with open('.env', 'w') as f:
            f.write(env_template)
        logger.info('Created .env file with template values')

def main():
    """Main setup function."""
    try:
        # Create directory structure
        create_directory_structure()
        
        # Create .env file
        create_env_file()
        
        # Setup package
        setup(
            name='moon-crypto',
            version='0.1.0',
            packages=find_packages(),
            install_requires=[
                line.strip()
                for line in open('requirements.txt')
                if line.strip() and not line.startswith('#')
            ],
            author='ohlulu',
            description='A cryptocurrency investment analysis tool',
            python_requires='>=3.8',
        )
        
        logger.info('Setup completed successfully!')
        
    except Exception as e:
        logger.error(f'Setup failed: {str(e)}')
        sys.exit(1)

if __name__ == '__main__':
    main() 