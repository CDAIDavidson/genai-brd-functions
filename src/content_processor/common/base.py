from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional, Literal, TypedDict, Union, List
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
    IN_PROGRESS = 'in progress'
    COMPLETED = 'completed'
    FAILED = 'failed'

class PubSubMessage:
    """Standard structure for Pub/Sub messages across the application"""
    
    def __init__(
        self,
        brd_workflow_id: str,
        document_id: str,
        data: Optional[Dict[str, Any]] = None,
        processing_complete: bool = False
    ):
        self.brd_workflow_id = brd_workflow_id
        self.document_id = document_id
        self.data = data or {}
        self.processing_complete = processing_complete
        self.timestamp = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for Pub/Sub publishing"""
        message = {
            "brd_workflow_id": self.brd_workflow_id,
            "document_id": self.document_id,
            "timestamp": self.timestamp,
            "processing_complete": self.processing_complete
        }
        
        # Include data if provided
        if self.data:
            message["data"] = self.data
            
        return message
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PubSubMessage':
        """Create a PubSubMessage from a dictionary"""
        return cls(
            brd_workflow_id=data.get("brd_workflow_id"),
            document_id=data.get("document_id"),
            data=data.get("data"),
            processing_complete=data.get("processing_complete", False)
        )
    
    @classmethod
    def from_cloud_event(cls, cloud_event: Dict[str, Any]) -> 'PubSubMessage':
        """Create a PubSubMessage from a Cloud Function event"""
        import base64
        import json
        
        if cloud_event and "message" in cloud_event and "data" in cloud_event["message"]:
            message_data = cloud_event["message"]["data"]
            
            # Check if it's a string that needs decoding
            if isinstance(message_data, str):
                try:
                    decoded_data = base64.b64decode(message_data).decode('utf-8')
                    message_dict = json.loads(decoded_data)
                except Exception:
                    # Try parsing directly if base64 decode fails
                    message_dict = json.loads(message_data)
            else:
                message_dict = message_data
                
            return cls.from_dict(message_dict)
        
        # Return a default message if parsing fails
        return cls("unknown_workflow_id", "unknown_document_id")

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