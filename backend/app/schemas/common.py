from pydantic import BaseModel, Field


class Page[T](BaseModel):
    items: list[T]
    page: int
    page_size: int
    total: int
    total_pages: int


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorEnvelope(BaseModel):
    success: bool = False
    error: ErrorBody


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, description="1-based page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


def build_page[T](items: list[T], page: int, page_size: int, total: int) -> Page[T]:
    return Page[T](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size if page_size else 0,
    )
