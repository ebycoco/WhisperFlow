"""
WhisperFlow — Entry Point
Initializes settings and logging, then starts the application.
"""

import sys
import multiprocessing

from src.config.settings import Settings, get_logs_dir
from src.utils.logger import setup_logger
from src.app import App

def main():
    """Main application entry point."""
    # PyInstaller multiprocessing support (needed for faster-whisper/torch sometimes)
    multiprocessing.freeze_support()
    
    # Setup centralized logging
    logger = setup_logger("WhisperFlow", log_dir=get_logs_dir(), level="INFO")
    logger.info("=" * 50)
    logger.info("WhisperFlow starting up")
    logger.info("=" * 50)

    try:
        # Load settings
        settings = Settings()
        
        # Create and start app
        app = App(settings)
        app.start()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
