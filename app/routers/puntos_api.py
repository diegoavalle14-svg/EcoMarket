from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.tables import points
from app.utils.security import require_admin

router = APIRouter()

# GET todos los puntos → usuarios y admin
@router.get("/puntos", tags=["Puntos"])
async def get_points(db: AsyncSession = Depends(get_db)):
    try:
        query = select(points)
        result = await db.execute(query)
        rows = result.fetchall()
        return {"points": [dict(row._mapping) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# POST crear punto de recolección → solo admin
@router.post("/puntos")
async def create_point(
    nombre: str = Form(...),
    direccion: str = Form(...),
    lat: str = Form(...),
    lng: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin)
):
    try:
        new_point = points.insert().values(
            nombre=nombre,
            direccion=direccion,
            lat=float(lat),
            lng=float(lng)
        )
        await db.execute(new_point)
        await db.commit()
        return {"message": "Punto de recolección creado exitosamente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# PUT actualizar punto → solo admin
@router.put("/puntos/{punto_id}")
async def update_point(
    punto_id: int,
    nombre: str = Form(...),
    direccion: str = Form(...),
    lat: str = Form(...),
    lng: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(require_admin)
):
    try:
        # Verificar que existe
        check_query = select(points).where(points.c.id == punto_id)
        check_result = await db.execute(check_query)
        existing = check_result.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Punto no encontrado")
        
        # Actualizar
        update_query = points.update().where(points.c.id == punto_id).values(
            nombre=nombre,
            direccion=direccion,
            lat=float(lat),
            lng=float(lng)
        )
        await db.execute(update_query)
        await db.commit()
        
        return {"message": "Punto actualizado exitosamente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# DELETE punto → solo admin
@router.delete("/puntos/{punto_id}")
async def delete_point(punto_id: int, db: AsyncSession = Depends(get_db), user=Depends(require_admin)):
    try:
        # Verificar que existe
        check_query = select(points).where(points.c.id == punto_id)
        check_result = await db.execute(check_query)
        existing = check_result.fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Punto no encontrado")
        
        # Eliminar
        query = points.delete().where(points.c.id == punto_id)
        await db.execute(query)
        await db.commit()
        return {"message": "Punto eliminado exitosamente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
