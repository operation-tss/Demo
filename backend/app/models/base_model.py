from datetime import datetime, timezone
from typing import Any, Optional
from sqlmodel import SQLModel as BaseSQLModel
from pydantic import model_validator, model_serializer

class SQLModel(BaseSQLModel):
    """
    Standard SQLModel augmented with Global UTC synchronization.
    Ensures every clinical timestamp is serialized with the 'Z' marker matching Healthcare Connect.
    """
    
    @model_validator(mode="before")
    @classmethod
    def ensure_aware_utc_global(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
            
        for k, v in data.items():
            if isinstance(v, str) and len(v) >= 10 and '-' in v and ':' in v:
                if '+' not in v and 'Z' not in v.upper():
                    data[k] = v + 'Z'
        return data

    @model_serializer(mode="wrap")
    def serialize_utc_global(self, handler, _info):
        result = handler(self)
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, datetime):
                    result[k] = self._ensure_z_suffix(v)
                elif isinstance(v, str) and '-' in v and ':' in v and 'T' in v:
                    if '+' not in v and 'Z' not in v.upper():
                        result[k] = v + 'Z'
        return result

    @staticmethod
    def _ensure_z_suffix(dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return f"{dt.isoformat()}Z"
        return dt.isoformat().replace('+00:00', 'Z')
