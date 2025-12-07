from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database.connection import get_db
from app.utils.security import get_current_user

router = APIRouter(prefix="/products", tags=["Productos Usuario"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def list_products(
    request: Request,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    # Obtener usuario actual usando la misma sesión
    user = await get_current_user(request, db)

    base_query = "SELECT * FROM products"
    values: dict = {}

    if category:
        base_query += " WHERE category = :category"
        values["category"] = category

    result = await db.execute(text(base_query), values)
    productos = result.fetchall()

    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "products": productos,
            "category": category,
            "user": user,
        },
    )

