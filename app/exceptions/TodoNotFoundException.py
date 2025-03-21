from fastapi import HTTPException, status


class TodoNotFoundException(HTTPException):
    def __init__(self, id: int = None):
        detail = 'Todo not found.'
        if id:
            detail = f'Todo with ID: {id} not found.'
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )