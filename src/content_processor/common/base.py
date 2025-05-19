from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional, Literal, TypedDict, Union, List
from datetime import datetime
from enum import Enum
from time import sleep

# Configure logger
logging.basicConfig(level=logging.INFO)

class DocumentType(str, Enum):
    DOCUMENT_TABLE_DATA = 'document_table_data'
    DOCUMENT_TABLES_DATA = 'document_tables_data'
    DOCUMENT_REQUIREMENT_DATA = 'document_requirement_data'
    DOCUMENT_SUMMARY_DATA = 'document_summary_data'
    FUNCTION_EXECUTION_DATA = 'function_execution_data'

class FunctionStatus(str, Enum):
    IN_PROGRESS = 'in progress'
    COMPLETED = 'completed'
    FAILED = 'failed'

class FunctionData(TypedDict):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str
    status: str  # Should be one of FunctionStatus values

class BrdSummaryData(TypedDict):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str

class BrdTableData(TypedDict):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str

class BrdRequirementData(TypedDict):
    timestamp_created: str
    timestamp_updated: str
    description_heading: str
    description: str

class Document:
    """Document class for Firestore storage"""
    
    def __init__(
        self,
        item_type: DocumentType,
        brd_workflow_id: str,
        timestamp_created: str,
        timestamp_updated: str,
        description: str,
        description_heading: str,
        item: Dict[str, Any],
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
        """Convert document to dictionary for Firestore storage"""
        doc_dict = {
            "item_type": self.item_type.value,
            "brd_workflow_id": self.brd_workflow_id,
            "description": self.description,
            "description_heading": self.description_heading,
            "item": self.item
        }
        
        # Include ID only if it exists
        if self.id:
            doc_dict["id"] = self.id
            
        return doc_dict
    
    @classmethod
    def create_document(
        cls,
        brd_workflow_id: str,
        status: FunctionStatus,
        description: str = "",
        description_heading: str = "",
        environment: str = "unknown",
        id: Optional[str] = None,
        **extras: Any
    ) -> 'Document':
        """Create a function execution document"""
        sleep(5)
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Create base function data
        function_data = {
            "timestamp_created": timestamp,
            "timestamp_updated": timestamp,
            "description_heading": description_heading,
            "description": description,
            "status": status.value,
            "environment": environment
        }
        
        # Add any extra fields
        function_data.update(extras)
        
        return cls(
            id=id,
            item_type=DocumentType.FUNCTION_EXECUTION_DATA,
            brd_workflow_id=brd_workflow_id,
            timestamp_created=timestamp,
            timestamp_updated=timestamp,
            description=description,
            description_heading=description_heading,
            item={"function_data": function_data}
        )

    @classmethod
    def update_document(
        cls,
        document: 'Document',
        status: Optional[FunctionStatus] = None,
        **extras: Any
    ) -> 'Document':
        """Update an existing function execution document
        
        Only updates status, timestamp_updated, and item fields
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Update timestamp at the parent level
        document.timestamp_updated = timestamp
        
        # Get existing function data
        function_data = document.item.get("function_data", {})
        
        # Update timestamp in function_data
        function_data["timestamp_updated"] = timestamp
        
        # Update status if provided
        if status is not None:
            function_data["status"] = status.value
        
        # Add any extra fields
        function_data.update(extras)
        
        # Update the document item
        document.item["function_data"] = function_data
        
        return document
    
    @classmethod
    def add_item_object(
        cls,
        document_id: str,
        key_name: str = "function_data",
        value: Dict[str, Any] = {}
    ) -> Dict[str, Any]:
        """Add an object to the item dictionary of a Document
        
        Args:
            document_id: The ID of the document to update
            key_name: The key name in the item dictionary (default: function_data)
            value: The object value to add (default: {})
            
        Returns:
            The updated item dictionary
        """
        item = {}
        item[key_name] = value
        return item 