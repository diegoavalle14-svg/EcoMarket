# admin_products.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.tables import products
from app.utils.security import require_admin
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/admin_productos/api", tags=["Productos Admin"])

# -----------------------
#  MODELOS
# -----------------------
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    price: float
    stock: int
    status: str
    image_url: Optional[str] = None


# -----------------------
#  GET - todos
# -----------------------
@router.get("/all")
async def get_all_products(user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        query = select(products)
        result = await db.execute(query)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
#  GET - individual
# -----------------------
@router.get("/{id}")
async def get_product(id: int, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        query = select(products).where(products.c.id == id)
        result = await db.execute(query)
        producto = result.fetchone()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return dict(producto._mapping)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
#  POST - crear
# -----------------------
@router.post("/create")
async def create_product(data: ProductBase, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        query = products.insert().values(
            name=data.name,
            description=data.description,
            category=data.category,
            price=data.price,
            stock=data.stock,
            status=data.status,
            image_url=data.image_url
        )
        result = await db.execute(query)
        await db.commit()
        return {
            "msg": "Producto creado",
            "id": result.inserted_primary_key[0]
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
#  PUT - actualizar
# -----------------------
@router.put("/{id}")
async def update_product(id: int, data: ProductBase, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        # Verificar que exista
        check_query = select(products).where(products.c.id == id)
        check_result = await db.execute(check_query)
        existing = check_result.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Actualizar
        update_query = products.update().where(products.c.id == id).values(
            name=data.name,
            description=data.description,
            category=data.category,
            price=data.price,
            stock=data.stock,
            status=data.status,
            image_url=data.image_url
        )
        await db.execute(update_query)
        await db.commit()

        return {"msg": "Producto actualizado"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------
#  DELETE - eliminar
# -----------------------
@router.delete("/{id}")
async def delete_product(id: int, user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        # Verificar que exista
        check_query = select(products).where(products.c.id == id)
        check_result = await db.execute(check_query)
        existing = check_result.fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Eliminar
        delete_query = products.delete().where(products.c.id == id)
        await db.execute(delete_query)
        await db.commit()

        return {"msg": "Producto eliminado"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
