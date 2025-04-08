import logging
from pathlib import Path
from src.utils.config import Paths

def setup_logging(level=logging.INFO):
    log_path = Paths.PROJECT_ROOT / "pipeline.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )