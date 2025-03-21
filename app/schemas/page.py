from math import ceil
from typing import Generic, List, TypeVar

from pydantic import BaseModel


T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    page_number: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


    @classmethod
    def create(cls, items: List[T], page_number: int, page_size: int, total_items: int):
        total_pages = int(ceil(total_items /page_size))
        return cls(
            items=items,
            page_number=page_number,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page_number < total_pages - 1,
            has_previous=page_number > 0)
    
