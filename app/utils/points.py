from sqlalchemy.ext.asyncio import AsyncSession
from app.database.tables import user_points, points_history

async def add_points(
    db: AsyncSession,
    user_id: int,
    cambio: int,
    motivo: str,
    referencia: str | None = None
):
    """
    Suma (o resta) puntos al usuario y registra el movimiento en el historial.
    cambio: entero (positivo = gana puntos, negativo = gasta puntos).
    """
    # Leer saldo actual
    result = await db.execute(
        user_points.select().where(user_points.c.user_id == user_id)
    )
    saldo_row = result.fetchone()
    saldo_dict = dict(saldo_row._mapping) if saldo_row else None
    balance = saldo_dict["balance"] if saldo_dict else 0
    nuevo_balance = balance + cambio

    # Actualizar o crear saldo
    if saldo_dict:
        await db.execute(
            user_points.update()
            .where(user_points.c.id == saldo_dict["id"])
            .values(balance=nuevo_balance)
        )
    else:
        await db.execute(
            user_points.insert().values(user_id=user_id, balance=nuevo_balance)
        )

    # Guardar en historial
    await db.execute(
        points_history.insert().values(
            user_id=user_id,
            cambio=cambio,
            motivo=motivo,
            referencia=referencia,
        )
    )

    await db.commit()

    return nuevo_balance

