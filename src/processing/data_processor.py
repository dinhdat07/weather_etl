# src/processing/data_processor.py
from typing import List, Dict, Tuple, Any
from ..storage.cache.city_cache import CityCache
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, table_config: Dict, city_cache: CityCache):
        self.config = table_config
        self.city_cache = city_cache
    
    def prepare_data(self, data_list: List[Dict]) -> Tuple[List[List], Dict]:
        results = {
            "total": len(data_list),
            "processed": 0,
            "inserted": 0,
            "skipped": 0,
            "errors": []
        }
        validated_data = []
        
        for idx, data in enumerate(data_list):
            try:
                params = self._process_record(data)
                validated_data.append(params)
                results["processed"] += 1
            except Exception as e:
                self._log_error(results, idx, data, e)
                continue
        
        return validated_data, results
    
    def _process_record(self, data: Dict) -> List[Any]:
        self._validate_required_fields(data)
        data['city_id'] = self._get_city_id(data)
        
        # prepare params in correct order
        return [
            data.get(field) 
            for field in self.config['fields_order']
        ]
    
    def _validate_required_fields(self, data: Dict):
        missing = [
            field for field in self.config['required'] 
            if field not in data
        ]
        if missing:
            raise ValueError(f"Missing required fields to get city_id: {missing}")
    
    def _get_city_id(self, data: Dict) -> int:
        return self.city_cache.get_city_id(
            city_name=data['city'],
            country=data['country'],
            lat=data['lat'],
            lon=data['lon']
        )
    
    def _log_error(self, results: Dict, idx: int, data: Dict, error: Exception):
        logger.error(
            f"Failed to process record {idx}: {str(error)}",
            extra={"data": data}
        )
        results["errors"].append({
            "record_index": idx,
            "record_id": data.get('city_id', 'unknown'),
            "error": str(error)
        })