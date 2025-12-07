from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.database.connection import SessionLocal
from app.database.tables import users


# ======================================================
# OBTENER USUARIO DESDE COOKIES
# ======================================================
async def get_current_user(request: Request):
    """Obtiene el usuario desde la cookie 'user_name'."""
    username = request.cookies.get("user_name")

    if not username:
        return None

    query = users.select().where(users.c.usuario == username)
    user = await database.fetch_one(query)

    return user


# ======================================================
# VERIFICAR QUE SEA ADMIN (MODO ESTRICTO, CON EXCEPCIÓN)
# ======================================================
async def admin_required(request: Request):
    """Lanza error si no es admin (uso interno si quieres usar HTTPException)."""

    username = request.cookies.get("user_name")

    if not username:
        raise HTTPException(status_code=401, detail="No autenticado")

    user = await database.fetch_one(
        users.select().where(users.c.usuario == username)
    )

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado (solo admin)")

    return user


# ======================================================
# VERIFICAR ADMIN PERO REDIRIGIENDO A LOGIN
# (ESTO SE USA EN PRODUCTOS)
# ======================================================
async def get_current_admin(request: Request):
    """Verifica que el usuario sea admin. Si no, lo redirige al login."""

    username = request.cookies.get("user_name")

    # Si no hay cookie → login
    if not username:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Buscar usuario
    user = await database.fetch_one(
        users.select().where(users.c.usuario == username)
    )

    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)

    # Verificar role
    if user["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)

    return user
