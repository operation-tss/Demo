from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

T = TypeVar("T")

class DataResponse(BaseModel, Generic[T]):
    """
    Standard Enterprise Response Envelope matching Healthcare Connect.
    Guarantees consistent { success, message, data } structure across all endpoints.
    """
    success: bool = True
    message: Optional[str] = "Operation successful"
    data: Optional[T] = None
