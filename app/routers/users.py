from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import SessionLocal, get_db
from app.database.tables import users
from app.utils.security import require_admin, hash_password
from app.utils.points import add_points

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# GET /register → muestra formulario HTML
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# POST /register-form → procesa formulario de registro
@router.post("/register-form")
@router.post("/register")
async def register_form(
    fullname: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirmPassword: str = Form(...),
    db: AsyncSession = Depends(get_db)  # ✅ AQUÍ: inyectar la sesión
):
    if password != confirmPassword:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")

    # Validar duplicados
    existing_user = await db.execute(users.select().where(users.c.usuario == username))
    if existing_user.fetchone():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    existing_email = await db.execute(users.select().where(users.c.email == email))
    if existing_email.fetchone():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    # Guardar usuario y obtener id
    result = await db.execute(
        users.insert().values(
            nombre_completo=fullname,
            usuario=username,
            email=email,
            password=hash_password(password),
            role="user",
        )
    )
    await db.commit()
    user_id = result.inserted_primary_key[0]

    # ➕ Puntos por registro
    await add_points(db, user_id, 20, "Registro de cuenta", "registro")

    return RedirectResponse(url="/auth/login", status_code=303)


# ====== ADMIN: CRUD USUARIOS ======

@router.get("/admin/users")
async def admin_list_users(
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    query = users.select().order_by(users.c.id.desc())
    result = await db.execute(query)
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/admin/users")
async def admin_create_user(
    request: Request,
    nombre_completo: str = Form(...),
    usuario: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    # Validar duplicados
    existing_user = await db.execute(users.select().where(users.c.usuario == usuario))
    if existing_user.fetchone():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    existing_email = await db.execute(users.select().where(users.c.email == email))
    if existing_email.fetchone():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    await db.execute(
        users.insert().values(
            nombre_completo=nombre_completo,
            usuario=usuario,
            email=email,
            password=hash_password(password),
            role=role,
        )
    )
    await db.commit()
    return {"ok": True}


@router.post("/admin/users/{user_id}")
async def admin_update_user(
    user_id: int,
    nombre_completo: str = Form(...),
    usuario: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    password: str = Form(""),
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    # Comprobar que existe
    existing = await db.execute(users.select().where(users.c.id == user_id))
    if not existing.fetchone():
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    valores = {
        "nombre_completo": nombre_completo,
        "usuario": usuario,
        "email": email,
        "role": role,
    }
    if password.strip():
        valores["password"] = hash_password(password)

    # Validar duplicados (usuario/email de otros ids)
    dup_user = await db.execute(
        users.select().where(users.c.usuario == usuario, users.c.id != user_id)
    )
    if dup_user.fetchone():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    dup_email = await db.execute(
        users.select().where(users.c.email == email, users.c.id != user_id)
    )
    if dup_email.fetchone():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    await db.execute(
        users.update().where(users.c.id == user_id).values(**valores)
    )
    await db.commit()
    return {"ok": True}


@router.delete("/admin/users/{user_id}")
async def admin_delete_user(
    user_id: int,
    admin=Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(users.delete().where(users.c.id == user_id))
    await db.commit()
    return {"ok": True}

