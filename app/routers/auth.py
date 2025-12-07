from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime
from starlette.status import HTTP_303_SEE_OTHER
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
import re
from pydantic import ValidationError
from app.database.connection import get_db
from app.database.tables import users, points_history
from app.utils.security import hash_password, verify_password
from app.utils.points import add_points

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")


# -------------------------------
# Mostrar login
# -------------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# -------------------------------
# Procesar login
# -------------------------------
@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    query = users.select().where(users.c.usuario == username)
    result = await db.execute(query)
    user_row = result.fetchone()

    if not user_row:
        return RedirectResponse(
            url="/auth/login?error=UsuarioNoExiste",
            status_code=HTTP_303_SEE_OTHER
        )

    user = dict(user_row._mapping)

    if not verify_password(password, user["password"]):
        return RedirectResponse(
            url="/auth/login?error=ContraseñaIncorrecta",
            status_code=HTTP_303_SEE_OTHER
        )

    # ➕ Puntos por login diario (+2 puntos si es su primer login del día)
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())

    result = await db.execute(
        points_history.select().where(
            (points_history.c.user_id == user["id"]) &
            (points_history.c.motivo == "Login diario") &
            (points_history.c.fecha >= today_start)
        )
    )
    last_login_today = result.fetchone()

    if not last_login_today:
        await add_points(db, user["id"], 2, "Login diario", "login")

    # Login exitoso → crear cookie
    redirect_url = "/menu" if user["role"] == "admin" else "/"

    response = RedirectResponse(url=redirect_url, status_code=HTTP_303_SEE_OTHER)
    response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    response.set_cookie(key="user_name", value=user["usuario"], httponly=True)
    response.set_cookie(key="role", value=user["role"], httponly=True)
    return response


# -------------------------------
# Mostrar registro
# -------------------------------
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# -------------------------------
# Procesar registro
# -------------------------------
@router.post("/register")
async def register_user(
    request: Request,
    nombre_completo: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # ---------- VALIDACIONES DE CAMPOS ----------
    # Nombre completo: mínimo 3 caracteres, solo letras y espacios
    nombre_limpio = nombre_completo.strip()
    if len(nombre_limpio) < 3:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "El nombre completo debe tener al menos 3 caracteres."},
            status_code=400,
        )
    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñ ]+", nombre_limpio):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "El nombre completo solo puede contener letras y espacios."},
            status_code=400,
        )

    # Username: 3–20 caracteres, solo letras, números y guion bajo, sin espacios
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "El nombre de usuario debe tener entre 3 y 20 caracteres y solo puede contener letras, números y guion bajo (sin espacios).",
            },
            status_code=400,
        )

    # Email: formato básico y longitud máxima
    email = email.strip()
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.fullmatch(email_regex, email):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "El correo electrónico no tiene un formato válido."},
            status_code=400,
        )
    if len(email) > 254:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "El correo electrónico es demasiado largo."},
            status_code=400,
        )

    # Contraseña: 10–64 caracteres, al menos una letra y un número
    if len(password) < 10 or len(password) > 64:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "La contraseña debe tener entre 10 y 64 caracteres."},
            status_code=400,
        )
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "La contraseña debe incluir al menos una letra y un número."},
            status_code=400,
        )

    # Confirmación
    if password != confirmPassword:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Las contraseñas no coinciden",
            },
            status_code=400,
        )

    # ---------- VALIDACIONES CONTRA LA BD ----------
    result = await db.execute(
        users.select().where(users.c.usuario == username)
    )
    existing_user_row = result.fetchone()
    existing_user = dict(existing_user_row._mapping) if existing_user_row else None
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "El usuario ya existe",
            },
            status_code=400,
        )

    result = await db.execute(
        users.select().where(users.c.email == email)
    )
    existing_email_row = result.fetchone()
    existing_email = dict(existing_email_row._mapping) if existing_email_row else None
    if existing_email:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "El email ya está registrado",
            },
            status_code=400,
        )

    hashed_password = hash_password(password)

    result = await db.execute(
        users.insert().values(
            nombre_completo=nombre_completo,
            usuario=username,
            password=hashed_password,
            email=email,
            role="user",
        )
    )
    await db.commit()
    user_id = result.lastrowid

    await add_points(db, user_id, 20, "Registro de cuenta", "registro")

    # Redirigir al login al terminar
    return RedirectResponse(
        url="/auth/login",
        status_code=status.HTTP_302_FOUND,
    )


# -------------------------------
# Logout
# -------------------------------
@router.get("/logout")
async def logout():
    redirect = RedirectResponse(url="/", status_code=303)
    redirect.delete_cookie("user_id")
    redirect.delete_cookie("user_name")
    redirect.delete_cookie("role")
    return redirect

