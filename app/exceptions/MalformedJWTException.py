from fastapi import HTTPException, status


class MalformedJWTException(HTTPException):
    def __init__(self, message: str = None):
        detail = 'Malformed JWT token.'
        if message:
            detail = message
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )