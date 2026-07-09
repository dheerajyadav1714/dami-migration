# agents/parsers/base_parser.py
from abc import ABC, abstractmethod
import pandas as pd

class BaseParser(ABC):
    """Abstract base class for all inventory parsers."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        
    @abstractmethod
    def parse(self, df: pd.DataFrame) -> list:
        """Parses a DataFrame and returns a list of normalized server dictionaries."""
        pass
        
    def _determine_workload(self, name: str) -> str:
        """Heuristic for determining workload type from server name."""
        name_upper = str(name).upper()
        if "LB" in name_upper: return "LB"
        if "WEB" in name_upper: return "WEB"
        if "APP" in name_upper: return "APP"
        if "DB" in name_upper: return "DB"
        if "CACHE" in name_upper: return "CACHE"
        if "QUEUE" in name_upper: return "QUEUE"
        if "INFRA" in name_upper: return "INFRA"
        return "DEV"
        
    def _determine_environment(self, name: str) -> str:
        """Heuristic for determining environment from server name."""
        name_upper = str(name).upper()
        if "PROD" in name_upper or "PRD" in name_upper: return "prod"
        if "STAGE" in name_upper or "STG" in name_upper: return "staging"
        if "TEST" in name_upper or "TST" in name_upper: return "test"
        return "dev"
