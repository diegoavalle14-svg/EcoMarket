from datetime import datetime
from sqlalchemy import (
    DateTime, Float, Table, Column, Integer, String,
    ForeignKey, Boolean, MetaData, Text, func,
)

# Crear metadata aqui directamente
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre_completo", String(150), nullable=False),
    Column("usuario", String(50), unique=True),
    Column("email", String(100), unique=True),
    Column("password", String(255)),
    Column("role", String(20), default="user"),
)

products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(100), nullable=False),
    Column("description", Text),
    Column("category", String(50), nullable=False),
    Column("price", Float, nullable=False),
    Column("stock", Integer, nullable=False, default=0),
    Column("status", String(50), default="disponible"),
    Column("owner_id", Integer),
    Column("image_url", String(500)),
    Column("created_at", DateTime, server_default=func.now()),
)

clients = Table(
    "clients",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(100)),
    Column("apellido", String(100)),
    Column("email", String(100)),
    Column("telefono", String(50)),
)

puntos = Table(
    "puntos_recoleccion",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(255)),
    Column("direccion", String(255)),
    Column("telefono", String(50)),
    Column("horario", String(255)),
)

solicitudes = Table(
    "solicitudes",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("producto", String(255), nullable=False),
    Column("cantidad", Integer, nullable=False),
    Column("descripcion", Text, nullable=True),
    Column("estado", String(50), default="pendiente"),
    Column("tipo", String(20), nullable=False),
)

points = Table(
    "points",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(100)),
    Column("direccion", String(200)),
    Column("lat", Float),
    Column("lng", Float),
)

user_points = Table(
    "user_points",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("balance", Integer, nullable=False, default=0),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
)

rewards = Table(
    "rewards",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nombre", String(150), nullable=False),
    Column("descripcion", Text),
    Column("puntos_necesarios", Integer, nullable=False),
    Column("activo", Boolean, nullable=False, default=True),
    Column("created_at", DateTime, server_default=func.now()),
)

points_history = Table(
    "points_history",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("cambio", Integer, nullable=False),
    Column("motivo", String(150), nullable=False),
    Column("referencia", String(100)),
    Column("fecha", DateTime, server_default=func.now()),
)
