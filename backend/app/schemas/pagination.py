"""Schema-level pagination parameter helper.

Defines `PaginationParams` used by API endpoints to centralize paging
logic (page, page_size, offset). Kept in `app.schemas` so endpoints can
import it without pulling in `app.api.v1` package internals.
"""

class PaginationParams:
	def __init__(self, page: int = 1, page_size: int = 20):
		self.page = max(1, page)
		self.page_size = min(max(1, page_size), 100)
		self.offset = (self.page - 1) * self.page_size

__all__ = ["PaginationParams"]
