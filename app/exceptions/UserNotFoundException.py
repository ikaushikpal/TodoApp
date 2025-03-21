from fastapi import HTTPException, status


class UserNotFoundException(HTTPException):
    def __init__(self, id: int = None, email: str = None):
        detail = 'User not found.'
        if id:
            detail = f'User with ID: {id} not found.'
        if email:
            detail = f'User with Email: {email} not found.'
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )