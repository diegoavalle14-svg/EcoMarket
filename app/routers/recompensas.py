from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.tables import user_points, rewards, points_history
from app.utils.security import require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


PUNTOS_POR_SOLICITUD_APROBADA = 10  # lo usarás luego en solicitudes_admin si quieres


# GET datos de recompensas del usuario (saldo + historial + catálogo)
@router.get("/mis-datos")
async def mis_datos_recompensas(user=Depends(require_login), db: AsyncSession = Depends(get_db)):
    try:
        user_id = user["id"]

        # Saldo actual
        saldo_query = select(user_points).where(user_points.c.user_id == user_id)
        saldo_result = await db.execute(saldo_query)
        saldo_row = saldo_result.fetchone()
        
        if saldo_row:
            balance = dict(saldo_row._mapping).get("balance", 0)
        else:
            balance = 0

        # Historial (últimos 20 movimientos)
        hist_query = (
            select(points_history)
            .where(points_history.c.user_id == user_id)
            .order_by(points_history.c.fecha.desc())
            .limit(20)
        )
        historial_result = await db.execute(hist_query)
        historial_rows = historial_result.fetchall()
        historial = [dict(row._mapping) for row in historial_rows]

        # Catálogo de recompensas activas
        rewards_query = (
            select(rewards)
            .where(rewards.c.activo == True)
            .order_by(rewards.c.puntos_necesarios)
        )
        catalogo_result = await db.execute(rewards_query)
        catalogo_rows = catalogo_result.fetchall()
        catalogo = [dict(row._mapping) for row in catalogo_rows]

        return {
            "balance": balance,
            "historial": historial,
            "rewards": catalogo,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# POST canjear recompensa
@router.post("/recompensas/canjear/{reward_id}")
async def canjear_recompensa(
    reward_id: int,
    user=Depends(require_login),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_id = user["id"]

        # Obtener recompensa
        reward_query = select(rewards).where(rewards.c.id == reward_id)
        reward_result = await db.execute(reward_query)
        reward = reward_result.scalars().first()

        if not reward:
            raise HTTPException(status_code=404, detail="Recompensa no encontrada")

        # Obtener saldo del usuario
        saldo_query = select(user_points).where(user_points.c.user_id == user_id)
        saldo_result = await db.execute(saldo_query)
        saldo_row = saldo_result.scalars().first()

        if not saldo_row or saldo_row.balance < reward.puntos_necesarios:
            raise HTTPException(status_code=400, detail="Puntos insuficientes")

        # Restar puntos
        new_balance = saldo_row.balance - reward.puntos_necesarios
        update_balance = user_points.update().where(
            user_points.c.user_id == user_id
        ).values(balance=new_balance)
        await db.execute(update_balance)

        # Registrar en historial
        insert_history = points_history.insert().values(
            user_id=user_id,
            tipo="canje",
            puntos=-reward.puntos_necesarios,
            descripcion=f"Canje de: {reward.nombre}"
        )
        await db.execute(insert_history)

        await db.commit()

        return {
            "message": f"Recompensa canjeada: {reward.nombre}",
            "nuevo_balance": new_balance
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# GET página HTML de recompensas
@router.get("/recompensas", response_class=HTMLResponse)
async def recompensas_page(request: Request, user=Depends(require_login)):
    return templates.TemplateResponse("recompensas.html", {"request": request})

