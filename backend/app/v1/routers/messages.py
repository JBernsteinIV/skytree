from internal.systemctl import  ( _internal_journalctl_get_messages )
from typing import Optional, List, Union
from fastapi import APIRouter

router = APIRouter()

@router.get("/messages/{unit}", tags=["messages"])
def get_messages(unit: str, since: Optional[str] = None, limit: Optional[int] = None) -> Union[List[dict],None]:
    messages = _internal_journalctl_get_messages(unit_name=unit, since=since, limit=limit)
    if len(messages) > 0:
        return messages
    else:
        if since == None:
            since = "today"
        return [f"No messages found since {since}"]