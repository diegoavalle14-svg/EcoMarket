from app.utils.security import hash_password

# Cambia "TuContraseñaSegura" por la contraseña real del admin
hashed = hash_password("Ecomarket2025!")
print(hashed)