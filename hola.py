# simple_compare.py

import mariadb
import redis
import time
import hashlib
import random

# --- 1. CONFIGURACIÓN DE LAS BASES DE DATOS ---
try:
    # Conexión a Redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping() # Verifica la conexión

    # Conexión a MariaDB
    conn = mariadb.connect(
        user="root", 
        password="666", 
        host="127.0.0.1",
        port=3306, 
        database="JWT"
    )
    cursor = conn.cursor()
    print("✅ Conexiones a MariaDB y Redis exitosas.")

except Exception as e:
    print(f"❌ Error al conectar a la base de datos: {e}")
    exit()

def hash_password(password):
    """Función simple para hashear la contraseña."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- 2. LA PRUEBA DE RENDIMIENTO ---

def run_test(iterations=100):
    """Ejecuta pruebas de escritura y lectura y muestra los promedios."""
    print(f"\n--- Ejecutando {iterations} pruebas de rendimiento ---")
    
    mariadb_write_times = []
    redis_write_times = []
    mariadb_read_times = []
    redis_read_times = []

    for i in range(iterations):
        # Generamos un usuario único para cada prueba
        username = f"user_simple_{i}_{random.randint(1000, 9999)}"
        password_hash = hash_password("password123")

        # --- Prueba de Escritura ---
        
        # MariaDB
        start = time.perf_counter()
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", 
                       (username, f"{username}@test.com", password_hash))
        conn.commit()
        mariadb_write_times.append((time.perf_counter() - start) * 1000)

        # Redis
        start = time.perf_counter()
        redis_client.hset(f"user:{username}", "password_hash", password_hash)
        redis_write_times.append((time.perf_counter() - start) * 1000)

        # --- Prueba de Lectura ---
        
        # MariaDB
        start = time.perf_counter()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
        cursor.fetchone()
        mariadb_read_times.append((time.perf_counter() - start) * 1000)

        # Redis
        start = time.perf_counter()
        redis_client.hget(f"user:{username}", "password_hash")
        redis_read_times.append((time.perf_counter() - start) * 1000)

    # --- 3. MOSTRAR RESULTADOS ---

    print("\n--- Resultados Promedio (en milisegundos) ---")
    
    print("\n-- Prueba de Escritura --")
    print(f"   💾 MariaDB (promedio): {sum(mariadb_write_times) / iterations:.4f} ms")
    print(f"   ⚡ Redis (promedio):   {sum(redis_write_times) / iterations:.4f} ms")
    
    print("\n-- Prueba de Lectura --")
    print(f"   💾 MariaDB (promedio): {sum(mariadb_read_times) / iterations:.4f} ms")
    print(f"   ⚡ Redis (promedio):   {sum(redis_read_times) / iterations:.4f} ms")

# --- 4. EJECUTAR EL SCRIPT ---
if __name__ == "__main__":
    run_test()
    # Cerramos la conexión a la base de datos al final
    conn.close()