# src/extraction/utils.py
from typing import Dict

class APIUtils:
    @staticmethod
    def is_api_success(response: Dict) -> bool:
        cod = response.get("cod")
        return str(cod) == "200" if cod else True