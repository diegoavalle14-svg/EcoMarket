from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import engine, SessionLocal, get_db, ensure_database_exists, create_tables
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.products import router as products_router
from app.routers.admin_productos import router as admin_products_router
from app.routers import puntos_api
from app.routers.solicitudes import router as solicitudes_router

from app.utils.security import (
    get_current_user,
    require_login,
    require_admin,
    RequiresLogin,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # -- Startup --
    print("[EcoMarket] Verificando base de datos...")
    ensure_database_exists()
    print("[EcoMarket] Creando tablas si no existen...")
    await create_tables()
    print("[EcoMarket] Servidor listo.")
    yield
    # -- Shutdown --
    await engine.dispose()
    print("[EcoMarket] Conexion cerrada.")


app = FastAPI(title="EcoMarket API", lifespan=lifespan)


@app.exception_handler(RequiresLogin)
async def requires_login_handler(request: Request, exc: RequiresLogin):
    return RedirectResponse(url="/auth/login")


templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/productos", response_class=HTMLResponse)
async def productos_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    return templates.TemplateResponse("productos.html", {"request": request, "user": user})


@app.get("/solicitudes", response_class=HTMLResponse)
async def solicitudes_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        raise RequiresLogin()
    return templates.TemplateResponse("solicitudes.html", {"request": request, "user": user})


@app.get("/puntos-recoleccion", response_class=HTMLResponse)
async def puntos_usuario_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    return templates.TemplateResponse("puntos_usuario.html", {"request": request, "user": user})


@app.get("/menu", response_class=HTMLResponse)
async def admin_menu(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user or user["role"] != "admin":
        raise RequiresLogin()

    puntos_info = {
        "registro": {"nombre": "Registro de nuevo usuario", "puntos": 20},
        "login": {"nombre": "Login diario", "puntos": 2},
        "solicitud": {"nombre": "Crear solicitud", "puntos": 5},
        "aprobado": {"nombre": "Solicitud aprobada", "puntos": 10},
    }
    return templates.TemplateResponse(
        "menu.html",
        {"request": request, "user": user, "puntos_info": puntos_info},
    )


@app.get("/admin_productos", response_class=HTMLResponse)
async def admin_productos_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user or user["role"] != "admin":
        raise RequiresLogin()
    return templates.TemplateResponse("admin_products.html", {"request": request, "user": user})


@app.get("/puntos-recoleccion-admin", response_class=HTMLResponse)
async def puntos_admin_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user or user["role"] != "admin":
        raise RequiresLogin()
    return templates.TemplateResponse("puntos_recoleccion.html", {"request": request, "user": user})


@app.get("/solicitudes-admin", response_class=HTMLResponse)
async def solicitudes_admin_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user or user["role"] != "admin":
        raise RequiresLogin()
    return templates.TemplateResponse("solicitudes_admin.html", {"request": request, "user": user})


@app.get("/gestion-usuarios", response_class=HTMLResponse)
async def gestion_usuarios_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    admin = await get_current_user(request, db)
    if not admin or admin["role"] != "admin":
        raise RequiresLogin()
    return templates.TemplateResponse("gestion_usuarios.html", {"request": request, "user": admin})


@app.get("/recompensas", response_class=HTMLResponse)
async def recompensas_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user:
        raise RequiresLogin()
    return templates.TemplateResponse("recompensas.html", {"request": request, "user": user})


@app.get("/admin-recompensas", response_class=HTMLResponse)
async def admin_recompensas_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await get_current_user(request, db)
    if not user or user["role"] != "admin":
        raise RequiresLogin()
    return templates.TemplateResponse("admin_recompensas.html", {"request": request, "user": user})


app.include_router(puntos_api.router, prefix="/api", tags=["Puntos API"])
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(users_router, prefix="", tags=["Usuarios"])
app.include_router(products_router, tags=["Productos Usuario"])
app.include_router(admin_products_router, tags=["Productos Admin"])
app.include_router(solicitudes_router, prefix="/solicitudes", tags=["Solicitudes"])

from app.routers.recompensas import router as recompensas_router
from app.routers.admin_recompensas import router as admin_recompensas_router

app.include_router(recompensas_router, prefix="/recompensas", tags=["Recompensas Usuario"])
app.include_router(admin_recompensas_router, tags=["Recompensas Admin"])
