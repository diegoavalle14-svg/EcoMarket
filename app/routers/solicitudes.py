from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database.connection import get_db
from app.database.tables import solicitudes, users
from app.utils.security import require_login, require_admin
from app.utils.points import add_points


router = APIRouter(tags=["Solicitudes"])


class SolicitudCreate(BaseModel):
    producto: str
    cantidad: int
    descripcion: str | None = None
    tipo: str | None = None


# GET mis solicitudes (usuario logueado)
@router.get("/mis-solicitudes")
async def mis_solicitudes(user=Depends(require_login), db: AsyncSession = Depends(get_db)):
    try:
        query = select(solicitudes).where(solicitudes.c.user_id == user["id"])
        result = await db.execute(query)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# POST crear solicitud (usuario logueado)
@router.post("/crear")
async def crear_solicitud(
    solicitud: SolicitudCreate,
    user=Depends(require_login),
    db: AsyncSession = Depends(get_db)
):
    try:
        new_solicitud = solicitudes.insert().values(
            user_id=user["id"],
            producto=solicitud.producto,
            cantidad=solicitud.cantidad,
            descripcion=solicitud.descripcion,
            tipo=solicitud.tipo or "donar",
            estado="pendiente"
        )
        await db.execute(new_solicitud)
        await db.commit()
        return {"message": "Solicitud creada exitosamente", "status": "pendiente"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# GET todas las solicitudes (solo admin)
@router.get("/admin")
async def get_all_solicitudes(user=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        query = (
            select(
                solicitudes.c.id,
                solicitudes.c.producto,
                solicitudes.c.cantidad,
                solicitudes.c.descripcion,
                solicitudes.c.tipo,
                solicitudes.c.estado,
                users.c.email,
            )
            .select_from(solicitudes.join(users, solicitudes.c.user_id == users.c.id))
            .order_by(solicitudes.c.id.desc())
        )
        result = await db.execute(query)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# PUT actualizar estado de solicitud (solo admin)
@router.put("/{solicitud_id}")
async def actualizar_solicitud(
    solicitud_id: int,
    estado: str,
    user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Obtener solicitud
        query = select(solicitudes).where(solicitudes.c.id == solicitud_id)
        result = await db.execute(query)
        solicitud = result.fetchone()

        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        # Actualizar estado
        update_query = (
            solicitudes
            .update()
            .where(solicitudes.c.id == solicitud_id)
            .values(estado=estado)
        )

        await db.execute(update_query)

        # Si fue aprobada, agregar puntos al usuario
        if estado == "aprobada":
            data = dict(solicitud._mapping)
            await add_points(
                db,
                data["user_id"],
                10,
                "Solicitud aprobada",
                referencia=str(solicitud_id)
            )

        await db.commit()

        return {"message": f"Solicitud actualizada a {estado}"}
    except Exception as e:
        await db.rollback()
        print("ERROR actualizar_solicitud:", e)
        raise HTTPException(status_code=400, detail=str(e))


# DELETE solicitud (solo admin)

@router.delete("/{solicitud_id}")
async def eliminar_solicitud(
    solicitud_id: int,
    user = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Verificar que la solicitud exista
        query = select(solicitudes).where(solicitudes.c.id == solicitud_id)
        result = await db.execute(query)
        solicitud = result.fetchone()

        if not solicitud:
            raise HTTPException(status_code=404, detail="Solicitud no encontrada")

        # Eliminar la solicitud
        stmt = (
            delete(solicitudes)
            .where(solicitudes.c.id == solicitud_id)
        )
        await db.execute(stmt)
        await db.commit()

        return {"message": f"Solicitud {solicitud_id} eliminada correctamente"}
    except Exception as e:
        await db.rollback()
        print("ERROR eliminar_solicitud:", e)
        raise HTTPException(status_code=400, detail=str(e))

