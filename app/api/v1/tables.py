from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_role
from app.models.table import Table
from app.models.user import User
from app.repositories.table_repository import table_repository
from app.schemas.table import TableCreate, TableResponse, TableStatusUpdate, TableUpdate
from app.services.table_service import table_service

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.get(
    "/",
    response_model=list[TableResponse],
    summary="List all tables",
)
async def list_tables(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Table]:
    """Return every dining table registered in the system."""
    return await table_repository.get_all(db)


@router.get(
    "/available",
    response_model=list[TableResponse],
    summary="List available tables",
)
async def list_available(
    min_capacity: int = 1,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Table]:
    """Return free tables with at least *min_capacity* seats."""
    return await table_service.get_available(db, min_capacity)


@router.get(
    "/{table_id}",
    response_model=TableResponse,
    summary="Get a single table",
)
async def get_table(
    table_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Table:
    """Return a table by its primary key, or 404 if not found."""
    table = await table_repository.get(db, table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table {table_id} not found")
    return table


@router.post(
    "/",
    response_model=TableResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new table",
)
async def create_table(
    data: TableCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
) -> Table:
    """Register a new dining table. Table number must be unique."""
    return await table_service.create_table(db, data)


@router.put(
    "/{table_id}",
    response_model=TableResponse,
    summary="Update a table",
)
async def update_table(
    table_id: int,
    data: TableUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin", "manager")),
) -> Table:
    """Update any fields of an existing table."""
    table = await table_repository.get(db, table_id)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table {table_id} not found")
    return await table_repository.update(db, table, data.model_dump(exclude_unset=True))


@router.patch(
    "/{table_id}/status",
    response_model=TableResponse,
    summary="Update table status",
)
async def update_table_status(
    table_id: int,
    data: TableStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Table:
    """Change the availability status of a table (free, occupied, reserved, maintenance)."""
    return await table_service.update_status(db, table_id, data.status)


@router.delete(
    "/{table_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a table",
)
async def delete_table(
    table_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> Response:
    """Permanently remove a table record. Requires admin role."""
    deleted = await table_repository.delete(db, table_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table {table_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
