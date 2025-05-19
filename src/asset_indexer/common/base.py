from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional, Literal, TypedDict, Union
from datetime import datetime
from enum import Enum

# Configure logger
logging.basicConfig(level=logging.INFO)

class DocumentType(str, Enum):
    DOCUMENT_TABLE_DATA = 'document_table_data'
    DOCUMENT_TABLES_DATA = 'document_tables_data'
    DOCUMENT_REQUIREMENT_DATA = 'document_requirement_data'
    DOCUMENT_SUMMARY_DATA = 'document_summary_data'
    FUNCTION_EXECUTION_DATA = 'function_execution_data'

class FunctionStatus(str, Enum):
    IN_PROGRESS = 'inprogress'
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
    def __init__(
        self, 
        id: str, 
        item_type: DocumentType,
        brd_workflow_id: str,
        description: str,
        description_heading: str,
        item: Dict[str, Any]
    ):
        self.id = id
        self.item_type = item_type
        self.brd_workflow_id = brd_workflow_id
        self.description = description
        self.description_heading = description_heading
        self.item = item
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary for Firestore storage"""
        return {
            "id": self.id,
            "item_type": self.item_type.value,
            "brd_workflow_id": self.brd_workflow_id,
            "description": self.description,
            "description_heading": self.description_heading,
            "item": self.item
        }
    
    @classmethod
    def create_function_execution(
        cls,
        id: str, 
        brd_workflow_id: str,
        status: FunctionStatus,
        description: str = "",
        description_heading: str = "",
        **extras: Any
    ) -> 'Document':
        """Create a function execution document"""
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        function_data = FunctionData(
            timestamp_created=timestamp,
            timestamp_updated=timestamp,
            description_heading=description_heading,
            description=description,
            status=status.value,
            **extras
        )
        
        return cls(
            id=id,
            item_type=DocumentType.FUNCTION_EXECUTION_DATA,
            brd_workflow_id=brd_workflow_id,
            description=description,
            description_heading=description_heading,
            item={"function_data": function_data}
        )

class BaseFunction(ABC):
    """Base class for all Cloud Functions"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def run(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Main function logic to be implemented by subclasses.
        
        Args:
            data: The event payload
            context: The event context
            
        Returns:
            Function result
        """
        pass
    
    async def execute(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute the function with logging and error handling.
        
        Args:
            data: The event payload
            context: The event context
            
        Returns:
            Function result
        """
        self.logger.info(f"Executing function with data: {data}")
        try:
            result = await self.run(data, context)
            self.logger.info(f"Function executed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Function execution failed: {str(e)}")
            raise 