import asyncio
from app.database.connection import engine
from app.database.tables import points

puntos = [
    {"nombre": "Kiosco Reciclaje Multiplaza", "direccion": "Mall Multiplaza, Tegucigalpa", "lat": 14.0874, "lng": -87.1903},
    {"nombre": "Centro Reciclaje UNAH", "direccion": "Ciudad Universitaria UNAH", "lat": 14.0847, "lng": -87.1633},
    {"nombre": "Estación Verde Parque Central", "direccion": "Plaza Central Francisco Morazán", "lat": 14.1060, "lng": -87.2045},
    {"nombre": "Punto Limpio Cascadas", "direccion": "Cascadas Mall, Blvd. Fuerzas Armadas", "lat": 14.0673, "lng": -87.2098},
    {"nombre": "Centro Comunal Kennedy", "direccion": "Primera entrada Col. Kennedy", "lat": 14.0725, "lng": -87.1686},
    {"nombre": "EcoEstación Metromall", "direccion": "Metromall, Blvd. FF.AA.", "lat": 14.0782, "lng": -87.2141},
    {"nombre": "Punto Ecológico Picacho", "direccion": "Parque Nacional El Picacho", "lat": 14.1167, "lng": -87.1931},
    {"nombre": "Reciclaje CCG", "direccion": "Centro Cívico Gubernamental", "lat": 14.0905, "lng": -87.1895},
    {"nombre": "Estación Morazán", "direccion": "Blvd. Morazán, frente a Plaza Criolla", "lat": 14.0963, "lng": -87.1862},
    {"nombre": "City Eco Puntos", "direccion": "City Mall Tegucigalpa", "lat": 14.0689, "lng": -87.2215},
]

async def seed():
    try:
        async with engine.begin() as conn:
            for p in puntos:
                await conn.execute(points.insert().values(**p))
        print("¡Éxito! 10 puntos de recolección en Tegucigalpa han sido insertados.")
    except Exception as e:
        print("Error insertando puntos:", e)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
