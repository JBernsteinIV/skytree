from internal.systemctl import  ( _internal_get_properties, _internal_systemctl_get_units )
from fastapi import APIRouter

router = APIRouter()

""" Returns a list of all systemd units of type 'timer'."""
@router.get("/timers", tags=["timers"])
def get_timers():
    timers = _internal_systemctl_get_units(unit_type='timer')
    return timers

@router.get("/timers/{timer}", tags=["timers"])
def get_timers(timer: str):
    if 'timer' not in timer:
        if '.' in timer:
            timer = timer.split('.')[0]
        timer += '.timer'
        properties = _internal_get_properties(unit_name=timer)
        return properties