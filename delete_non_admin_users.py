# delete_non_admin_users.py
import asyncio
from app.database.connection import database
from app.database.tables import users, products

async def delete_non_admin():
    await database.connect()
    
    try:
        # Primero, obtener los IDs de usuarios que NO son admin
        non_admin_users = await database.fetch_all(
            users.select().where(users.c.role != "admin")
        )
        
        if not non_admin_users:
            print("✅ No hay usuarios no-admin para eliminar")
            return
        
        user_ids = [user["id"] for user in non_admin_users]
        print(f"📋 Se encontraron {len(user_ids)} usuarios no-admin")
        
        # Eliminar o actualizar productos asociados a estos usuarios
        # Opción 1: Eliminar los productos
        delete_products = products.delete().where(products.c.owner_id.in_(user_ids))
        products_deleted = await database.execute(delete_products)
        print(f"🗑️  Se eliminaron {products_deleted} productos asociados")
        
        # Opción 2: Si prefieres mantener los productos, descoméntalo y comenta la opción 1
        # update_products = products.update().where(
        #     products.c.owner_id.in_(user_ids)
        # ).values(owner_id=None)
        # await database.execute(update_products)
        # print(f"✏️  Se actualizaron los productos para quitar la referencia")
        
        # Ahora sí, eliminar los usuarios
        query = users.delete().where(users.c.role != "admin")
        result = await database.execute(query)
        
        print(f"✅ Se eliminaron {result} usuarios (admin se mantuvo)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await database.disconnect()

if __name__ == "__main__":
    asyncio.run(delete_non_admin())