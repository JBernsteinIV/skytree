from internal.systemctl import  ( _internal_get_properties, _internal_systemctl_get_units, _internal_get_unit_state_options )
from fastapi import APIRouter

router = APIRouter()

""" Returns a list of all systemd units of type 'service'."""
@router.get("/services", tags=["services"])
def get_services():
    services = _internal_systemctl_get_units(unit_type='service')
    return services

@router.get("/services/error", tags=["services"])
def get_options():
    options = _internal_get_unit_state_options()
    return options

# Scan systemctl for the current state of this service.
@router.get("/services/{service}", tags=["services"])
def check_service(service: str):
    properties = _internal_get_properties(unit_name=service)
    return properties

