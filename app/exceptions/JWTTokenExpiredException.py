from fastapi import HTTPException, status


class JWTTokenExpiredException(HTTPException):
    def __init__(self, token: str = None):
        detail = 'JWT Token has expired.'
        if token:
            detail = f'JWT Token: {token} has expired.'
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )
