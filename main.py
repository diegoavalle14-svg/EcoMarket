from fastapi import FastAPI, Form, Request, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr, BaseModel, validator
import databases
import sqlalchemy
from passlib.hash import argon2
import re

# -------------------------------
# Configuración MySQL
# -------------------------------
DATABASE_URL = "mysql+mysqlconnector://root:1234@localhost/ecomarketdb"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

# -------------------------------
# Tabla de usuarios
# -------------------------------
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("first_name", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("last_name", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("username", sqlalchemy.String(50), unique=True, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String(100), unique=True, nullable=False),
    sqlalchemy.Column("password", sqlalchemy.String(255), nullable=False),
)

# -------------------------------
# Tabla de productos
# -------------------------------
products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(100), nullable=False),
    sqlalchemy.Column("description", sqlalchemy.String(255)),
    sqlalchemy.Column("category", sqlalchemy.String(50), nullable=False),
    sqlalchemy.Column("status", sqlalchemy.String(20), default="disponible"),
    sqlalchemy.Column("owner_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
)

engine = sqlalchemy.create_engine(DATABASE_URL)
metadata.create_all(engine)

# -------------------------------
# FastAPI
# -------------------------------
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# -------------------------------
# Eventos startup/shutdown
# -------------------------------
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# -------------------------------
# Páginas
# -------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/menu", response_class=HTMLResponse)
async def menu(request: Request):
    return templates.TemplateResponse("menu.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# -------------------------------
# Registro de usuarios
# -------------------------------
@app.post("/register")
async def register_user(
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...)
):
    if len(password) > 72:
        raise HTTPException(status_code=400, detail="La contraseña no puede exceder 72 caracteres")

    existing_user = await database.fetch_one(users.select().where(users.c.username == username))
    existing_email = await database.fetch_one(users.select().where(users.c.email == email))

    if existing_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")
    if existing_email:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")

    hashed_password = argon2.hash(password)
    query = users.insert().values(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        username=username.strip(),
        email=email.strip(),
        password=hashed_password
    )
    await database.execute(query)
    return RedirectResponse(url="/", status_code=303)

# -------------------------------
# Login
# -------------------------------
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if not username.strip() or not password.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debe ingresar usuario y contraseña")

    user = await database.fetch_one(users.select().where(users.c.username == username))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    if not argon2.verify(password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Contraseña incorrecta")

    return RedirectResponse(url="/menu", status_code=303)

# -------------------------------
# Productos (público)
# -------------------------------
@app.get("/products-page", response_class=HTMLResponse)
async def products_page(request: Request):
    all_products = await database.fetch_all(products.select())
    return templates.TemplateResponse(
        "products.html",
        {"request": request, "products": all_products}
    )

@app.get("/products")
async def get_products(category: str = None):
    if category:
        query = products.select().where(products.c.category == category.lower())
    else:
        query = products.select()
    results = await database.fetch_all(query)
    return results

# -------------------------------
# Panel de administración de productos
# -------------------------------
@app.get("/admin/products", response_class=HTMLResponse)
async def admin_products_page(request: Request):
    all_products = await database.fetch_all(products.select())
    return templates.TemplateResponse(
        "admin_products.html",
        {"request": request, "products": all_products}
    )

@app.post("/admin/products")
async def admin_create_product(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    owner_id: int = Form(...),
):
    query = products.insert().values(
        name=name.strip(),
        description=description.strip(),
        category=category.strip().lower(),
        owner_id=owner_id
    )
    await database.execute(query)
    return RedirectResponse(url="/admin/products", status_code=303)
