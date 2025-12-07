# fix_passwords.py
import asyncio
from app.database.connection import database
from app.database.tables import users
from app.utils.security import hash_password

async def fix_passwords():
    await database.connect()
    
    # Diccionario con usuario: contraseña_en_texto_plano
    usuarios_a_actualizar = {
        "admin": "Ecomarket2025!",  # Cambia esto por tu contraseña real
        # Agrega más usuarios si los tienes
    }
    
    for username, plain_password in usuarios_a_actualizar.items():
        # Generar el hash correcto
        new_hash = hash_password(plain_password)
        
        # Actualizar en la base de datos
        query = users.update().where(
            users.c.usuario == username
        ).values(password=new_hash)
        
        result = await database.execute(query)
        print(f"✅ Contraseña actualizada para: {username}")
    
    await database.disconnect()
    print("\n🎉 Todas las contraseñas han sido actualizadas correctamente")

if __name__ == "__main__":
    asyncio.run(fix_passwords())