from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional, Literal, TypedDict, Union, List
from datetime import datetime
from enum import Enum
from time import sleep
from pydantic import BaseModel

# Configure logger
logging.basicConfig(level=logging.INFO)

class DocumentType(str, Enum):
    DOCUMENT_TABLE_DATA = "document_table_data"
    DOCUMENT_TABLES_DATA = "document_tables_data"
    DOCUMENT_REQUIREMENT_DATA = "document_requirement_data"
    DOCUMENT_SUMMARY_DATA = "document_summary_data"
    FUNCTION_EXECUTION_DATA = "function_execution_data"

class FunctionStatus(str, Enum):
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"
    FAILED = "failed"

class FunctionData(BaseModel):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str
    status: str
    working_on: str
    cloud_function_name: str


class BrdSummaryData(BaseModel):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str

class BrdTableData(BaseModel):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str

class BrdRequirementData(BaseModel):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str

# Define the union type for item data
ItemData = Union[
    Dict[Literal["function_data"], FunctionData],
    Dict[Literal["document_summary_data"], BrdSummaryData],
    Dict[Literal["document_tables_data"], BrdTableData],
    Dict[Literal["document_requirement_data"], BrdRequirementData],
    Dict[str, Any]  # This is equivalent to Record<string, unknown>
]

class DocumentClass:
    """Document class for Firestore storage"""
    
    def __init__(
        self, 
        item_type: DocumentType,
        brd_workflow_id: str,
        timestamp_created: str,
        timestamp_updated: str,
        description: str,
        description_heading: str,
        item: ItemData,
        id: Optional[str] = None
    ):
        self.id = id
        self.item_type = item_type
        self.brd_workflow_id = brd_workflow_id
        self.timestamp_created = timestamp_created
        self.timestamp_updated = timestamp_updated
        self.description = description
        self.description_heading = description_heading
        self.item = item
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the object to a dictionary for Firestore storage"""
        return {
            "id": self.id,
            "item_type": self.item_type,
            "brd_workflow_id": self.brd_workflow_id,
            "timestamp_created": self.timestamp_created,
            "timestamp_updated": self.timestamp_updated,
            "description": self.description,
            "description_heading": self.description_heading,
            "item": self.item
        }
    
    # Make this class behave like a dictionary for Firestore
    def items(self):
        """Return items for Firestore compatibility"""
        return self.to_dict().items()
    
    def __getitem__(self, key):
        """Allow dictionary-like access to properties"""
        return self.to_dict()[key]
    
    def get(self, key, default=None):
        """Dictionary-like get method"""
        return self.to_dict().get(key, default)

