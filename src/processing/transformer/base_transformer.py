from abc import ABC, abstractmethod
from typing import Dict, List, Any
import logging

class BaseTransformer(ABC):
    DEFAULT_COUNTRY = 'VN'
    UNKNOWN_CITY = 'Unknown'
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass
    
    def _transform_common_fields(self, row: Dict) -> Dict:
        return {
            'city': row.get('city', self.UNKNOWN_CITY),
            'lat': row.get('lat'),
            'lon': row.get('lon'),
            'country': row.get('country', self.DEFAULT_COUNTRY)
        }
    