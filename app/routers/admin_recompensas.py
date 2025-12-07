from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.database.tables import user_points, rewards, points_history, users
from app.utils.security import require_admin

router = APIRouter()


@router.get("/admin/rewards")
async def list_rewards(admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        query = select(rewards).order_by(rewards.c.id.desc())
        result = await db.execute(query)
        rows = result.fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/rewards")
async def create_reward(
    nombre: str = Form(...),
    puntos_necesarios: int = Form(...),
    descripcion: str = Form(""),
    activo: bool = Form(True),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        await db.execute(
            rewards.insert().values(
                nombre=nombre,
                descripcion=descripcion,
                puntos_necesarios=puntos_necesarios,
                activo=activo,
            )
        )
        await db.commit()
        return {"ok": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/rewards/{reward_id}")
async def update_reward(
    reward_id: int,
    nombre: str = Form(...),
    puntos_necesarios: int = Form(...),
    descripcion: str = Form(""),
    activo: bool = Form(True),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        row_query = select(rewards).where(rewards.c.id == reward_id)
        row_result = await db.execute(row_query)
        row = row_result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Recompensa no encontrada")

        await db.execute(
            rewards.update()
            .where(rewards.c.id == reward_id)
            .values(
                nombre=nombre,
                descripcion=descripcion,
                puntos_necesarios=puntos_necesarios,
                activo=activo,
            )
        )
        await db.commit()
        return {"ok": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/admin/rewards/{reward_id}")
async def delete_reward(reward_id: int, admin=Depends(require_admin), db: AsyncSession = Depends(get_db)):
    try:
        row_query = select(rewards).where(rewards.c.id == reward_id)
        row_result = await db.execute(row_query)
        row = row_result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Recompensa no encontrada")

        await db.execute(rewards.delete().where(rewards.c.id == reward_id))
        await db.commit()
        return {"ok": True}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/admin/users/{user_id}/ajustar-puntos")
async def ajustar_puntos(
    user_id: int,
    cambio: int = Form(...),
    motivo: str = Form(...),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Comprobar usuario
        user_query = select(users).where(users.c.id == user_id)
        user_result = await db.execute(user_query)
        user_row = user_result.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Saldo actual
        saldo_query = select(user_points).where(user_points.c.user_id == user_id)
        saldo_result = await db.execute(saldo_query)
        saldo_row = saldo_result.fetchone()
        
        balance = dict(saldo_row._mapping).get("balance", 0) if saldo_row else 0
        nuevo_balance = balance + cambio

        if nuevo_balance < 0:
            raise HTTPException(status_code=400, detail="El saldo no puede ser negativo")

        if saldo_row:
            await db.execute(
                user_points.update()
                .where(user_points.c.id == dict(saldo_row._mapping)["id"])
                .values(balance=nuevo_balance)
            )
        else:
            await db.execute(
                user_points.insert().values(user_id=user_id, balance=nuevo_balance)
            )

        # Historial
        await db.execute(
            points_history.insert().values(
                user_id=user_id,
                puntos=cambio,
                descripcion=motivo,
                tipo="ajuste_admin",
            )
        )
        
        await db.commit()
        return {"ok": True, "nuevo_balance": nuevo_balance}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
