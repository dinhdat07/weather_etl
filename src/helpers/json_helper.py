import json
import logging
from typing import Any, Dict, List
logger = logging.getLogger(__name__)

def load_json_file(filepath: str) -> List[Dict[str, Any]]:
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info(f"Loaded {len(data)} records from {filepath}")
            return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load {filepath}: {str(e)}")
        raise

def save_json_file(data: List[Dict[str, Any]], filepath: str) -> None:
    with open(filepath, 'w+', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} records to {filepath}")