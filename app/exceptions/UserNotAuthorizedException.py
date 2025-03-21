from fastapi import HTTPException, status


class UserNotAuthorizedException(HTTPException):
    def __init__(self, message: str = None):
        detail = 'User is not authorized.'
        if message:
            detail = message
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
