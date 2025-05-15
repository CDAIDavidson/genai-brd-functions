from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional

# Configure logger
logging.basicConfig(level=logging.INFO)

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