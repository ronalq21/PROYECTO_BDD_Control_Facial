# e:\FINESI 5\base de datos 2\segunda unidad\reconocimiento facil\database.py
import mysql.connector
import sys
from tkinter import messagebox
import datetime
import bcrypt # Importar bcrypt para hashear contraseñas

# --- Configuración de la Base de Datos ---
# Asegúrate de que estas credenciales sean correctas
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '', # Coloca tu contraseña aquí si tienes una
    'database': 'vdm'
}

def init_db():
    """
    Crea las tablas si no existen y añade un usuario de prueba si la tabla está vacía.
    """
    conn = None
    cursor = None
    try:
        # Conectar sin especificar la base de datos para poder crearla si no existe
        # Añadimos un timeout para que no se quede colgado indefinidamente si la BD no responde.
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'], 
            user=DB_CONFIG['user'], 
            password=DB_CONFIG['password'],
            connection_timeout=5  # Timeout de 5 segundos
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")

        # Crear tabla personas si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_completo VARCHAR(100) NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Crear tabla asistencia si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            id INT AUTO_INCREMENT PRIMARY KEY,
            persona_id INT,
            nombre_completo VARCHAR(100),
            fecha DATE NOT NULL,
            hora_entrada TIME NOT NULL,
            FOREIGN KEY (persona_id) REFERENCES personas (id)
        );
        """)

        # Crear tabla asistencia_salida si no existe
        # (La definición de esta tabla ya está en tu archivo SQL, la replicamos aquí para consistencia)
        # ... (puedes añadir la creación de asistencia_salida aquí si lo deseas)

        # Crear tabla usuarios si no existe
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre_usuario VARCHAR(50) NOT NULL UNIQUE,
            contrasena VARCHAR(255) NOT NULL,
            contrasena_plana VARCHAR(255) NULL, -- Columna para la contraseña en texto plano (NO RECOMENDADO), se permite que sea NULL.
            nombre VARCHAR(100) NOT NULL, 
            apellido VARCHAR(100) NOT NULL,
            dni VARCHAR(20) NOT NULL UNIQUE,
            correo VARCHAR(100) NULL, 
            celular VARCHAR(20) NULL,
            rol VARCHAR(20) DEFAULT 'user' NOT NULL
        );
        """)

        # --- VERIFICACIÓN Y REPARACIÓN DE LA TABLA usuarios ---
        # Esto soluciona el error si la tabla fue creada sin la columna 'contrasena_plana'.
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'contrasena_plana'
        """, (DB_CONFIG['database'],))
        if cursor.fetchone()[0] == 0:
            print("La columna 'contrasena_plana' no existe. Añadiéndola...")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN contrasena_plana VARCHAR(255) NULL AFTER contrasena;")
        
        # Verificación y reparación para la columna 'correo'
        cursor.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'correo'", (DB_CONFIG['database'],))
        if cursor.fetchone()[0] == 0:
            print("La columna 'correo' no existe. Añadiéndola...")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN correo VARCHAR(100) NULL AFTER dni;")

        # Verificación y reparación para la columna 'celular'
        cursor.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'celular'", (DB_CONFIG['database'],))
        if cursor.fetchone()[0] == 0:
            print("La columna 'celular' no existe. Añadiéndola...")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN celular VARCHAR(20) NULL AFTER correo;")

        # Verificación y reparación para la columna 'rol'
        cursor.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'usuarios' AND COLUMN_NAME = 'rol'", (DB_CONFIG['database'],))
        if cursor.fetchone()[0] == 0:
            print("La columna 'rol' no existe. Añadiéndola...")
            cursor.execute("ALTER TABLE usuarios ADD COLUMN rol VARCHAR(20) DEFAULT 'user' NOT NULL AFTER celular;")

        # Insertar usuario de prueba si la tabla está vacía
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            contrasena_plana = '75580218'
            contrasena_hashed = bcrypt.hashpw(contrasena_plana.encode('utf-8'), bcrypt.gensalt())
            sql_insert = """
                INSERT INTO usuarios (nombre_usuario, contrasena, contrasena_plana, nombre, apellido, dni, correo, celular, rol) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            # Se añaden valores para los nuevos campos del usuario de prueba
            cursor.execute(sql_insert, ('vidman', contrasena_hashed, contrasena_plana, 'vidman ruis', 'roque mamani', '75580218', 'vidman@example.com', '987654321', 'admin'))
            conn.commit()
            print("Usuario de prueba 'vidman' creado.")
    except mysql.connector.Error as err:
        # Este es el punto crítico. Si la BD no está disponible, mostramos un error y salimos.
        messagebox.showerror(
            "Error Crítico de Base de Datos",
            f"No se pudo conectar o inicializar la base de datos.\n\n"
            f"Error: {err}\n\n"
            "Por favor, asegúrate de que el servidor MySQL está en ejecución y las credenciales son correctas. La aplicacion se cerrara."
        )
        return False # Indica que la inicialización falló
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return True # Indica que la inicialización fue exitosa

def conectar_db():
    """Establece la conexión con la base de datos."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Base de Datos", f"No se pudo conectar a la base de datos: {err}")
        return None

def verificar_usuario(dni, contrasena_plana):
    """ 
    Verifica el DNI y la contraseña contra la base de datos.
    Usa bcrypt para una comparación segura.
    """
    conn = conectar_db()
    if conn is None:
        return False
    
    cursor = conn.cursor()
    try:
        sql = "SELECT contrasena, rol FROM usuarios WHERE dni = %s"
        cursor.execute(sql, (dni,))
        resultado = cursor.fetchone()

        if resultado:
            contrasena_hashed = resultado[0].encode('utf-8')
            rol = resultado[1]
            # Comprobar si la contraseña plana coincide con la hasheada
            if bcrypt.checkpw(contrasena_plana.encode('utf-8'), contrasena_hashed):
                return True, rol # Contraseña correcta, devuelve el rol
        return False, None # Usuario no encontrado o contraseña incorrecta
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Validación", f"Error al validar usuario: {err}")
        return False, None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def crear_usuario(nombre_usuario, contrasena_plana, nombre, apellido, dni, correo, celular, rol='user'):
    """
    Crea un nuevo usuario en la base de datos con una contraseña hasheada.
    Devuelve el ID del nuevo usuario si tiene éxito, de lo contrario None.
    """
    conn = conectar_db()
    if conn is None:
        return None

    cursor = conn.cursor()
    try:
        # Hashear la contraseña antes de guardarla
        contrasena_hashed = bcrypt.hashpw(contrasena_plana.encode('utf-8'), bcrypt.gensalt())
        sql = """
            INSERT INTO usuarios (nombre_usuario, contrasena, contrasena_plana, nombre, apellido, dni, correo, celular, rol) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (nombre_usuario, contrasena_hashed, contrasena_plana, nombre, apellido, dni, correo, celular, rol))
        conn.commit()
        new_user_id = cursor.lastrowid # Obtener el ID del usuario recién creado
        return new_user_id
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Creación", f"No se pudo crear el usuario: {err}")
        conn.rollback()
        return None
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def obtener_todos_los_usuarios():
    """
    Obtiene todos los usuarios de la base de datos, excluyendo la contraseña.
    """
    conn = conectar_db()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        sql = "SELECT id, nombre_usuario, contrasena_plana, nombre, apellido, dni, correo, celular, rol FROM usuarios ORDER BY id"
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Consulta", f"No se pudieron obtener los usuarios: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def actualizar_usuario(id_usuario, nombre_usuario, nombre, apellido, dni, correo, celular, rol, contrasena_plana=None):
    """
    Actualiza los datos de un usuario existente.
    Si se proporciona una nueva contraseña, la hashea y la actualiza.
    """
    conn = conectar_db()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        if contrasena_plana:
            # Si se proporcionó una nueva contraseña, la hasheamos
            contrasena_hashed = bcrypt.hashpw(contrasena_plana.encode('utf-8'), bcrypt.gensalt())
            sql = "UPDATE usuarios SET nombre_usuario = %s, nombre = %s, apellido = %s, dni = %s, correo = %s, celular = %s, rol = %s, contrasena = %s, contrasena_plana = %s WHERE id = %s"
            cursor.execute(sql, (nombre_usuario, nombre, apellido, dni, correo, celular, rol, contrasena_hashed, contrasena_plana, id_usuario))
        else:
            # Si no se proporcionó contraseña, actualizamos los otros datos incluyendo el rol
            sql = "UPDATE usuarios SET nombre_usuario = %s, nombre = %s, apellido = %s, dni = %s, correo = %s, celular = %s, rol = %s WHERE id = %s"
            cursor.execute(sql, (nombre_usuario, nombre, apellido, dni, correo, celular, rol, id_usuario))
        
        conn.commit()
        return True
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Actualización", f"No se pudo actualizar el usuario: {err}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def eliminar_usuario(id_usuario):
    """
    Elimina un usuario de la base de datos por su ID.
    """
    conn = conectar_db()
    if conn is None: return False
    cursor = conn.cursor()
    sql = "DELETE FROM usuarios WHERE id = %s"
    cursor.execute(sql, (id_usuario,))
    conn.commit()
    return cursor.rowcount > 0 # Devuelve True si se eliminó una fila

def registrar_y_obtener_persona(nombre_completo):
    """
    Registra una nueva persona en la tabla 'personas' y devuelve su ID autogenerado.
    Devuelve el ID de la nueva persona si tiene éxito, de lo contrario None.
    """
    conn = conectar_db()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO personas (nombre_completo) VALUES (%s)"
        cursor.execute(sql, (nombre_completo,))
        conn.commit()
        new_persona_id = cursor.lastrowid
        print(f"Persona '{nombre_completo}' registrada en tabla 'personas' con ID: {new_persona_id}")
        return new_persona_id
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Registro", f"No se pudo registrar a la persona en la base de datos: {err}")
        return None
    finally:
        cursor.close()
        conn.close()

def obtener_nombre_persona(persona_id):
    """
    Busca y devuelve el nombre completo de una persona por su ID.
    """
    conn = conectar_db()
    if conn is None:
        return "Error DB"

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT nombre_completo FROM personas WHERE id = %s", (persona_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else "ID no encontrado"
    except mysql.connector.Error as err:
        print(f"Error al obtener nombre: {err}")
        return "Error DB"
    finally:
        cursor.close()
        conn.close()

def registrar_asistencia(persona_id, nombre_completo):
    """
    Registra la entrada de una persona en la tabla de asistencia,
    evitando duplicados para el mismo día.
    """
    conn = conectar_db()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        fecha_actual = datetime.date.today()

        # 1. Verificar si ya existe un registro para esta persona hoy
        check_sql = "SELECT id FROM asistencia WHERE persona_id = %s AND fecha = %s"
        cursor.execute(check_sql, (persona_id, fecha_actual))
        if cursor.fetchone():
            # print(f"La asistencia para el ID {persona_id} ya fue registrada hoy.")
            return False # Ya existe, no hacer nada

        # 2. Si no existe, insertar el nuevo registro
        hora_actual = datetime.datetime.now().time()
        insert_sql = "INSERT INTO asistencia (persona_id, nombre_completo, fecha, hora_entrada) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_sql, (persona_id, nombre_completo, fecha_actual, hora_actual))
        conn.commit()
        return True # Se registró exitosamente
    except mysql.connector.Error as err:
        print(f"Error al registrar asistencia: {err}")
        conn.rollback() # Revertir cambios en caso de error
        return False
    finally:
        cursor.close()
        conn.close()

def registrar_asistencia_salida(persona_id, nombre_completo):
    """
    Registra la salida de una persona en la tabla de asistencia_salida,
    evitando duplicados para el mismo día.
    """
    conn = conectar_db()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        fecha_actual = datetime.date.today()

        # 1. Verificar si ya existe un registro de salida para esta persona hoy
        check_sql = "SELECT id FROM asistencia_salida WHERE persona_id = %s AND fecha = %s"
        cursor.execute(check_sql, (persona_id, fecha_actual))
        if cursor.fetchone():
            # print(f"La salida para el ID {persona_id} ya fue registrada hoy.")
            return False # Ya existe, no hacer nada

        # 2. Si no existe, insertar el nuevo registro
        hora_actual = datetime.datetime.now().time()
        insert_sql = "INSERT INTO asistencia_salida (persona_id, nombre_completo, fecha, hora_salida) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_sql, (persona_id, nombre_completo, fecha_actual, hora_actual))
        conn.commit()
        return True # Se registró exitosamente
    except mysql.connector.Error as err:
        print(f"Error al registrar salida: {err}")
        conn.rollback() # Revertir cambios en caso de error
        return False
    finally:
        cursor.close()
        conn.close()


def obtener_reporte_asistencia(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene un reporte consolidado de entradas y salidas.
    Si se proporcionan fecha_inicio y fecha_fin, filtra los resultados por ese rango.
    Calcula también las horas trabajadas.
    """
    conn = conectar_db()
    if conn is None:
        return [] # Devuelve una lista vacía si hay error de conexión

    cursor = conn.cursor(dictionary=True)
    try:
        # La función TIMEDIFF calcula la diferencia entre la hora de salida y la de entrada.
        # Si s.hora_salida es NULL, el resultado de TIMEDIFF también será NULL.
        sql = """
        SELECT 
            a.persona_id, 
            a.nombre_completo, 
            a.fecha, 
            a.hora_entrada, 
            s.hora_salida,
            TIMEDIFF(s.hora_salida, a.hora_entrada) AS horas_asistidas
        FROM asistencia a
        LEFT JOIN asistencia_salida s ON a.persona_id = s.persona_id AND a.fecha = s.fecha
        """
        params = []
        if fecha_inicio and fecha_fin:
            sql += " WHERE a.fecha BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        sql += " ORDER BY a.fecha DESC, a.hora_entrada DESC;"
        cursor.execute(sql, params)
        resultados = cursor.fetchall()
        return resultados
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Reporte", f"No se pudo generar el reporte: {err}")
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_todas_las_personas():
    """
    Obtiene todas las personas registradas para reconocimiento facial.
    """
    conn = conectar_db()
    if conn is None:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        # Ordenamos por ID descendente para ver los más nuevos primero
        sql = "SELECT id, nombre_completo, fecha_registro FROM personas ORDER BY id DESC"
        cursor.execute(sql)
        return cursor.fetchall()
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Consulta", f"No se pudieron obtener las personas registradas: {err}")
        return []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

def eliminar_persona_y_asistencia(persona_id):
    """
    Elimina una persona de la tabla 'personas' y todos sus registros
    asociados en 'asistencia' y 'asistencia_salida'.
    """
    conn = conectar_db()
    if conn is None:
        return False
    cursor = conn.cursor()
    try:
        # Es importante eliminar los registros de las tablas dependientes primero
        # para evitar errores de clave foránea.
        cursor.execute("DELETE FROM asistencia WHERE persona_id = %s", (persona_id,))
        cursor.execute("DELETE FROM asistencia_salida WHERE persona_id = %s", (persona_id,))
        
        # Ahora eliminamos a la persona de la tabla principal
        cursor.execute("DELETE FROM personas WHERE id = %s", (persona_id,))
        
        conn.commit()
        # rowcount > 0 en la última operación indica si se eliminó la persona.
        return cursor.rowcount > 0
    except mysql.connector.Error as err:
        messagebox.showerror("Error de Eliminación", f"No se pudo eliminar a la persona: {err}")
        conn.rollback()
        return False
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
