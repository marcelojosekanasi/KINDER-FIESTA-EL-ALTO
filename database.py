"""
KINDERFIESTA - Módulo de conexión a MySQL
Gestiona todas las operaciones con la base de datos
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Configuración de la BD
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'kinderfiesta'
}

def conectar():
    """Conecta a la base de datos"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Error de conexión: {e}")
        return None

# ============ SALONES ============

def obtener_todos_salones():
    """Obtiene TODOS los salones de la BD (visible e invisible)"""
    try:
        conn = conectar()
        if not conn:
            print("❌ No se pudo conectar a la BD")
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        # Consulta EXACTA a tu BD
        cursor.execute("""
    SELECT id, name, phone, whatsapp, google_maps, address, locationCode, category, rating, visible, folder, fotos
    FROM salones
    ORDER BY id DESC
""")

        
        salones = cursor.fetchall()
        cursor.close()
        conn.close()
        
        print(f"✅ Salones en BD: {len(salones)}")
        
        # Procesar datos y mapear para JavaScript
        for salon in salones:
            salon['salon_id'] = salon.get('id')
            salon['nombre'] = salon.get('name', 'Sin nombre')
            salon['telefono'] = salon.get('phone', 'N/A')
            salon['direccion'] = salon.get('address', 'Sin dirección')
            salon['zona'] = salon.get('locationCode', '')
            salon['categoria'] = salon.get('category', 'Salón Infantil')
            salon['promedio'] = float(salon.get('rating', 0)) if salon.get('rating') else 0
            salon['carpeta_fotos'] = salon.get('folder', f"salon{salon['id']}")
            salon['fotos'] = '1.jpg,2.jpg,3.jpg'
            salon['reviews'] = obtener_reviews_salon(salon['id'])
            salon['whatsapp'] = salon.get('whatsapp')
            salon['google_maps'] = salon.get('google_maps')

            
            print(f"  ✅ {salon['nombre']} - {len(salon['reviews'])} comentarios - Rating: {salon['promedio']}")
            
        return salones if salones else []
    except Error as e:
        print(f"❌ Error al obtener salones: {e}")
        return []

def obtener_salon_por_id(salon_id):
    """Obtiene un salón específico por ID"""
    try:
        conn = conectar()
        if not conn:
            return None
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                id, name, phone, address, locationCode, category, 
                rating, visible, folder
            FROM salones
            WHERE id = %s
        """, (salon_id,))
        
        salon = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if salon:
            salon['salon_id'] = salon.get('id')
            salon['nombre'] = salon.get('name', 'Sin nombre')
            salon['telefono'] = salon.get('phone', 'N/A')
            salon['direccion'] = salon.get('address', 'Sin dirección')
            salon['zona'] = salon.get('locationCode', '')
            salon['categoria'] = salon.get('category', 'Salón Infantil')
            salon['promedio'] = float(salon.get('rating', 0)) if salon.get('rating') else 0
            salon['carpeta_fotos'] = salon.get('folder', f"salon{salon['id']}")
            salon['fotos'] = '1.jpg,2.jpg,3.jpg'
            salon['reviews'] = obtener_reviews_salon(salon['id'])
            salon['whatsapp'] = salon.get('whatsapp')
            salon['google_maps'] = salon.get('google_maps')
            print(f"✅ Salón obtenido: {salon['nombre']}")
        
        return salon
    except Error as e:
        print(f"❌ Error al obtener salón: {e}")
        return None
        
    except Exception as e:
        print(f"❌ Error en buscar_salones: {e}")
        import traceback
        traceback.print_exc()
        return []

        
    except Exception as e:
        print(f"❌ Error en buscar_salones: {e}")
        import traceback
        traceback.print_exc()
        return []


def buscar_salones(query):
    """
    Buscar salones por nombre, ubicación o categoría
    INSENSIBLE A MAYÚSCULAS/MINÚSCULAS
    """
    try:
        conn = conectar()
        if not conn:
            print("❌ No se pudo conectar a la BD")
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        # Convertir búsqueda a minúsculas
        busqueda = f"%{query.lower()}%"
        
        # Consulta adaptada a tu estructura de BD
        query_sql = """
            SELECT 
                id, name, phone, address, locationCode, category, 
                rating, visible, folder
            FROM salones 
            WHERE visible = 1 
            AND (
                LOWER(name) LIKE %s 
                OR LOWER(address) LIKE %s 
                OR LOWER(category) LIKE %s
                OR LOWER(locationCode) LIKE %s
            )
            ORDER BY name ASC
        """
        
        # Ejecutar búsqueda
        cursor.execute(query_sql, (busqueda, busqueda, busqueda, busqueda))
        salones = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Búsqueda '{query}': {len(salones)} resultados encontrados")
        
        # Mapear datos para compatibilidad
        resultados = []
        for salon in salones:
            resultados.append({
                'id': salon['id'],
                'nombre': salon['name'],
                'telefono': salon['phone'],
                'direccion': salon['address'],
                'zona': salon['locationCode'],
                'categoria': salon['category'],
                'promedio': float(salon['rating']) if salon['rating'] else 0,
                'foto_principal': f"{salon['folder']}/1.jpg",
                'carpeta_fotos': salon['folder']
            })
            print(f"   - {salon['name']}")
        
        return resultados
        
    except Exception as e:
        print(f"❌ Error en buscar_salones: {e}")
        import traceback
        traceback.print_exc()
        return []

def obtener_horarios_salon(salon_id):
    """Obtiene los horarios de un salón"""
    try:
        conn = conectar()
        if not conn:
            return {}
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT dia, hora_apertura, hora_cierre, cerrado
            FROM horarios
            WHERE salon_id = %s
            ORDER BY FIELD(dia, 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo')
        """, (salon_id,))
        
        horarios_lista = cursor.fetchall()
        cursor.close()
        conn.close()
        
        horarios_dict = {}
        for h in horarios_lista:
            if h['cerrado']:
                horarios_dict[h['dia']] = 'Cerrado'
            else:
                apertura = ''
                cierre = ''
                
                if h['hora_apertura']:
                    if hasattr(h['hora_apertura'], 'strftime'):
                        apertura = h['hora_apertura'].strftime('%H:%M')
                    else:
                        apertura = str(h['hora_apertura'])
                
                if h['hora_cierre']:
                    if hasattr(h['hora_cierre'], 'strftime'):
                        cierre = h['hora_cierre'].strftime('%H:%M')
                    else:
                        cierre = str(h['hora_cierre'])
                
                if apertura and cierre:
                    horarios_dict[h['dia']] = f"{apertura} - {cierre}"
        
        return horarios_dict if horarios_dict else {}
    except Error as e:
        print(f"❌ Error al obtener horarios: {e}")
        return {}

# ============ REVIEWS ============

def obtener_reviews_salon(salon_id):
    """Obtiene reviews de un salón"""
    try:
        conn = conectar()
        if not conn:
            return []
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, comentario, rating, fecha
            FROM reviews
            WHERE salon_id = %s
            ORDER BY fecha DESC
        """, (salon_id,))
        
        reviews = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for review in reviews:
            if review['fecha']:
                review['fecha'] = review['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        return reviews if reviews else []
    except Error as e:
        print(f"❌ Error al obtener reviews: {e}")
        return []

def agregar_review(salon_id, nombre, comentario, rating):
    """Agrega un nuevo review"""
    try:
        conn = conectar()
        if not conn:
            return None, None
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            INSERT INTO reviews (salon_id, nombre, comentario, rating)
            VALUES (%s, %s, %s, %s)
        """, (salon_id, nombre, comentario, rating))
        
        conn.commit()
        review_id = cursor.lastrowid
        
        # Obtener el review insertado
        cursor.execute("""
            SELECT id, nombre, comentario, rating, fecha
            FROM reviews WHERE id = %s
        """, (review_id,))
        
        review = cursor.fetchone()
        if review and review['fecha']:
            review['fecha'] = review['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        
        # El rating se actualiza automáticamente por el TRIGGER
        cursor.execute("SELECT rating FROM salones WHERE id = %s", (salon_id,))
        salon_data = cursor.fetchone()
        nuevo_rating = float(salon_data['rating']) if salon_data and salon_data['rating'] else 0
        
        cursor.close()
        conn.close()
        
        print(f"✅ Review agregado al salón {salon_id}")
        return review, nuevo_rating
    except Error as e:
        print(f"❌ Error al agregar review: {e}")
        return None, None

def eliminar_review(salon_id, review_id):
    """Elimina un review"""
    try:
        conn = conectar()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM reviews
            WHERE id = %s AND salon_id = %s
        """, (review_id, salon_id))
        
        conn.commit()
        resultado = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        if resultado:
            print(f"✅ Review {review_id} eliminado")
        
        return resultado
    except Error as e:
        print(f"❌ Error al eliminar review: {e}")
        return False

def actualizar_review(salon_id, review_id, nuevo_comentario, nuevo_rating, nuevo_nombre=None):
    """Actualizar review con nombre opcional"""
    try:
        conn = conectar()
        cursor = conn.cursor()
        
        # Si se proporciona nuevo nombre, actualizarlo también
        if nuevo_nombre:
            cursor.execute("""
                UPDATE reviews 
                SET comentario = %s, rating = %s, nombre = %s
                WHERE id = %s AND salon_id = %s
            """, (nuevo_comentario, nuevo_rating, nuevo_nombre, review_id, salon_id))
        else:
            cursor.execute("""
                UPDATE reviews 
                SET comentario = %s, rating = %s
                WHERE id = %s AND salon_id = %s
            """, (nuevo_comentario, nuevo_rating, review_id, salon_id))
        
        conn.commit()
        
        # Recalcular promedio del salón
        nuevo_promedio = recalcular_promedio_salon(salon_id)
        
        # Obtener review actualizado
        cursor.execute("""
            SELECT id, nombre, comentario, rating, fecha 
            FROM reviews 
            WHERE id = %s
        """, (review_id,))
        
        review = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if review:
            return {
                'id': review[0],
                'nombre': review[1],
                'comentario': review[2],
                'rating': review[3],
                'fecha': review[4].isoformat()
            }
        return None
    except Exception as e:
        print(f"❌ Error al actualizar review: {e}")
        return None

def recalcular_promedio_salon(salon_id):
    """Recalcula el promedio de un salón"""
    try:
        conn = conectar()
        if not conn:
            return 0
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT AVG(rating) AS promedio FROM reviews WHERE salon_id = %s
        """, (salon_id,))
        
        resultado = cursor.fetchone()
        nuevo_promedio = round(resultado['promedio'], 1) if resultado['promedio'] else 0
        
        cursor.execute("""
            UPDATE salones SET rating = %s WHERE id = %s
        """, (nuevo_promedio, salon_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return nuevo_promedio
    except Error as e:
        print(f"❌ Error al recalcular promedio: {e}")
        return 0

# ============ SALONES ADMIN ============

def cambiar_visibilidad_salon(salon_id, visible):
    """Cambia visibilidad de un salón"""
    try:
        conn = conectar()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE salones SET visible = %s WHERE id = %s
        """, (int(visible), salon_id))
        
        conn.commit()
        resultado = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        estado = "visible" if visible else "oculto"
        print(f"✅ Salón {salon_id} ahora está {estado}")
        return resultado
    except Error as e:
        print(f"❌ Error al cambiar visibilidad: {e}")
        return False

def eliminar_salon(salon_id):
    """Elimina un salón permanentemente"""
    try:
        conn = conectar()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Los FOREIGN KEY con ON DELETE CASCADE se encargan de eliminar reviews y horarios
        cursor.execute("DELETE FROM salones WHERE id = %s", (salon_id,))
        
        conn.commit()
        resultado = cursor.rowcount > 0
        cursor.close()
        conn.close()
        
        if resultado:
            print(f"✅ Salón {salon_id} eliminado permanentemente")
        
        return resultado
    except Error as e:
        print(f"❌ Error al eliminar salón: {e}")
        return False

def agregar_salon_desde_solicitud(datos, carpeta_fotos):
    """Crea un salón desde una solicitud aprobada"""
    try:
        conn = conectar()
        if not conn:
            return None
        
        cursor = conn.cursor()
        
        # Insertar salón con whatsapp y google_maps
        cursor.execute("""
            INSERT INTO salones 
            (name, phone, whatsapp, google_maps, address, locationCode, category, rating, visible, folder)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 0, 1, %s)
        """, (
            datos.get('nombre', 'Sin nombre'),
            datos.get('telefono', ''),
            datos.get('whatsapp', ''),
            datos.get('google_maps', ''),
            datos.get('direccion', ''),
            datos.get('zona', ''),
            datos.get('categoria', 'Salón Infantil'),
            carpeta_fotos
        ))
        
        salon_id = cursor.lastrowid
        
        # Agregar horarios si existen (lista de objetos)
        horarios = datos.get('horarios', [])
        if horarios and isinstance(horarios, list):
            for h in horarios:
                dia = h.get('dia')
                apertura = h.get('apertura') or None
                cierre = h.get('cierre') or None
                cerrado = h.get('cerrado', False)
                
                if not dia:
                    continue
                
                if cerrado or not apertura or not cierre:
                    cursor.execute("""
                        INSERT INTO horarios (salon_id, dia, cerrado)
                        VALUES (%s, %s, 1)
                    """, (salon_id, dia))
                else:
                    cursor.execute("""
                        INSERT INTO horarios (salon_id, dia, hora_apertura, hora_cierre, cerrado)
                        VALUES (%s, %s, %s, %s, 0)
                    """, (salon_id, dia, apertura, cierre))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Salón {salon_id} creado desde solicitud")
        return salon_id
    except Error as e:
        print(f"❌ Error al agregar salón desde solicitud: {e}")
        return None


# ============ ADMIN ============

def verificar_credenciales_admin(email, password):
    """Verifica las credenciales de un administrador"""
    try:
        conn = conectar()
        if not conn:
            return False
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id FROM administradores
            WHERE email = %s AND password = %s
            LIMIT 1
        """, (email, password))
        
        resultado = cursor.fetchone() is not None
        cursor.close()
        conn.close()
        
        if resultado:
            print(f"✅ Admin {email} autenticado")
        
        return resultado
    except Error as e:
        print(f"❌ Error al verificar credenciales: {e}")
        return False

# ============================================
# FUNCIONES PARA USUARIOS Y TESTIMONIOS
# ============================================

def registrar_usuario(nombre, email, password):
    """Registrar nuevo usuario"""
    try:
        import bcrypt
        conn = conectar()  # ✅ CORREGIDO: era get_connection()
        if not conn:
            return None, "No se pudo conectar a la base de datos"
        
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el email ya existe
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return None, "El email ya está registrado"
        
        # Encriptar contraseña
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insertar usuario
        cursor.execute("""
            INSERT INTO usuarios (nombre, email, password, activo) 
            VALUES (%s, %s, %s, 1)
        """, (nombre, email, password_hash))
        
        conn.commit()
        user_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        print(f"✅ Usuario registrado: {email}")
        return user_id, "Usuario registrado exitosamente"
    except Exception as e:
        print(f"❌ Error al registrar usuario: {e}")
        return None, str(e)

def verificar_login(email, password):
    """Verificar credenciales de login"""
    try:
        import bcrypt
        conn = conectar()  # ✅ CORREGIDO: era get_connection()
        if not conn:
            return None, "No se pudo conectar a la base de datos"
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, nombre, email, password, activo 
            FROM usuarios 
            WHERE email = %s
        """, (email,))
        
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not usuario:
            return None, "Email no encontrado"
        
        if not usuario['activo']:
            return None, "Usuario desactivado"
        
        # Verificar contraseña
        if bcrypt.checkpw(password.encode('utf-8'), usuario['password'].encode('utf-8')):
            return {
                'id': usuario['id'],
                'nombre': usuario['nombre'],
                'email': usuario['email']
            }, "Login exitoso"
        else:
            return None, "Contraseña incorrecta"
    except Exception as e:
        print(f"❌ Error al verificar login: {e}")
        return None, str(e)

def agregar_testimonio(usuario_id, nombre_usuario, rating, comentario):
    """Agregar testimonio de usuario"""
    try:
        conn = conectar()  # ✅ CORREGIDO: era get_connection()
        if not conn:
            return None, "No se pudo conectar a la base de datos"
        
        cursor = conn.cursor(dictionary=True)
        
        # Insertar testimonio
        cursor.execute("""
            INSERT INTO testimonios (usuario_id, nombre_usuario, rating, comentario, aprobado) 
            VALUES (%s, %s, %s, %s, 1)
        """, (usuario_id, nombre_usuario, rating, comentario))
        
        conn.commit()
        testimonio_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        print(f"✅ Testimonio agregado por usuario {nombre_usuario}")
        return testimonio_id, "Testimonio agregado exitosamente"
    except Exception as e:
        print(f"❌ Error al agregar testimonio: {e}")
        return None, str(e)

def obtener_testimonios_aprobados(limite=10):
    """Obtener testimonios aprobados para mostrar en la página"""
    try:
        conn = conectar()
        if not conn:
            print("❌ No se pudo conectar a la BD")
            return []
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT t.id, t.usuario_id, t.nombre_usuario, t.rating, 
                   t.comentario, t.fecha, t.aprobado
            FROM testimonios t
            WHERE t.aprobado = 1
            ORDER BY t.fecha DESC
            LIMIT %s
        """, (limite,))
        
        testimonios = cursor.fetchall()
        
        # Formatear fechas para JSON
        for t in testimonios:
            if t.get('fecha'):
                if hasattr(t['fecha'], 'strftime'):
                    t['fecha'] = t['fecha'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    t['fecha'] = str(t['fecha'])
        
        cursor.close()
        conn.close()
        
        print(f"✅ Obtenidos {len(testimonios)} testimonios de la BD")
        return testimonios
        
    except Exception as e:
        print(f"❌ Error al obtener testimonios: {e}")
        import traceback
        traceback.print_exc()
        return []

def verificar_usuario_ya_comento(usuario_id):
    """Verificar si el usuario ya dejó un testimonio"""
    try:
        conn = conectar()  # ✅ CORREGIDO: era get_connection()
        if not conn:
            return False
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id FROM testimonios WHERE usuario_id = %s LIMIT 1
        """, (usuario_id,))
        
        resultado = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return resultado is not None
    except Exception as e:
        print(f"❌ Error al verificar testimonio: {e}")
        return False

# ============ PRUEBA DE CONEXIÓN ============

def test_connection():
    """Prueba la conexión a la base de datos"""
    try:
        conn = conectar()
        if conn and conn.is_connected():
            print("✅ Conectado a MySQL correctamente")
            
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()[0]
            print(f"✅ Base de datos: {db_name}")
            
            cursor.execute("SELECT COUNT(*) FROM salones")
            total_salones = cursor.fetchone()[0]
            print(f"✅ Total de salones: {total_salones}")
            
            cursor.close()
            conn.close()
            return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
    
    return False

def obtener_estadisticas():
    """
    Obtener estadísticas para la página de inicio
    """
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        
        estadisticas = {}
        
        # 1. Familias Conectadas (usuarios registrados)
        cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = 1")
        resultado = cursor.fetchone()
        estadisticas['familias'] = resultado['total'] if resultado else 0
        
        # 2. Salones Verificados (salones visibles)
        cursor.execute("SELECT COUNT(*) as total FROM salones WHERE visible = 1")
        resultado = cursor.fetchone()
        estadisticas['salones'] = resultado['total'] if resultado else 0
        
        # 3. Satisfacción de Clientes
        cursor.execute("SELECT AVG(rating) as promedio FROM reviews")
        resultado = cursor.fetchone()
        if resultado and resultado['promedio']:
            estadisticas['satisfaccion'] = round((resultado['promedio'] / 5) * 100)
        else:
            estadisticas['satisfaccion'] = 98
        
        # 4. Tiempo de respuesta
        estadisticas['tiempo_respuesta'] = "24h"
        
        cursor.close()
        conn.close()
        
        return estadisticas
        
    except Exception as e:
        print(f"❌ Error en obtener_estadisticas: {e}")
        return {
            'familias': 0,
            'salones': 0,
            'satisfaccion': 98,
            'tiempo_respuesta': '24h'
        }

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🧪 PROBANDO CONEXIÓN A LA BASE DE DATOS KINDERFIESTA")
    print("=" * 70)
    if test_connection():
        print("\n✅ Todo está funcionando correctamente!")
        print("\n" + "=" * 70)
        print("📊 SALONES DISPONIBLES:")
        print("=" * 70)
        salones = obtener_todos_salones()
        for s in salones:
            print(f"  ID: {s['id']} | Nombre: {s['nombre']} | Rating: {s['promedio']} ⭐ | Visible: {'Sí' if s['visible'] else 'No'}")
        print("=" * 70 + "\n")
    else:
        print("\n❌ No se pudo conectar a la base de datos")
        print("Verifica tu configuración en DB_CONFIG")
        print("=" * 70 + "\n")
