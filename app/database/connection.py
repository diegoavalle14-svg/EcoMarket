# -------------------------------
# Conexion a PostgreSQL (ASYNC)
# Auto-creacion de base de datos
# -------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Configuracion de BD
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "ecomarketdb")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Crear engine async
engine = create_async_engine(DATABASE_URL, echo=False)

# SessionLocal para async
SessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


# Funcion para obtener sesion async
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def ensure_database_exists():
    """
    Crea la base de datos si no existe.
    Usa una conexion sincrona temporal a la BD por defecto 'postgres'
    porque CREATE DATABASE no se puede ejecutar dentro de una transaccion async.
    """
    sync_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/postgres"
    sync_engine = create_engine(sync_url, isolation_level="AUTOCOMMIT")
    with sync_engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
            {"dbname": DB_NAME}
        )
        if not result.fetchone():
            # Escapar el nombre de la BD (no se puede parametrizar DDL)
            conn.execute(text(f'CREATE DATABASE "{DB_NAME}"'))
            print(f"[EcoMarket] Base de datos '{DB_NAME}' creada.")
        else:
            print(f"[EcoMarket] Base de datos '{DB_NAME}' ya existe.")
    sync_engine.dispose()


async def create_tables():
    """
    Crea todas las tablas definidas en tables.py si no existen.
    """
    from app.database.tables import metadata
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)
