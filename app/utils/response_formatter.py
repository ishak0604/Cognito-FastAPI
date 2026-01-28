from fastapi.responses import JSONResponse

def response(status_code: int, data: dict):
    return JSONResponse(
        status_code=status_code,
        content=data
    )
