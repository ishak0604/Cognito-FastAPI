"""Legacy combined auth_endpoints module.

This file has been split into multiple modules:
- app.api.v1.endpoints.signup
- app.api.v1.endpoints.login
- app.api.v1.endpoints.password

Keep this small shim for compatibility; new imports should use the split modules.
"""

from fastapi import APIRouter

router = APIRouter()

