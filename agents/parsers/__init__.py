# agents/parsers/__init__.py
from .base_parser import BaseParser
from .rvtools import RVToolsParser
from .aws import AWSParser
from .azure import AzureParser
from .device42 import Device42Parser

def get_parser(source_type: str, project_id: str) -> BaseParser:
    """Factory to return the appropriate parser based on source type."""
    source_type = source_type.lower().strip()
    if source_type == "vmware":
        return RVToolsParser(project_id)
    elif source_type == "aws":
        return AWSParser(project_id)
    elif source_type == "azure":
        return AzureParser(project_id)
    elif source_type == "device42":
        return Device42Parser(project_id)
    else:
        # Default fallback
        return RVToolsParser(project_id)
