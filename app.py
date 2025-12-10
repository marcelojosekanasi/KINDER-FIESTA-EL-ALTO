from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import database as db
import os
import json
import shutil
# ========== IMPORTS DE SEGURIDAD ==========
from security import (
    validar_email,
    sanitizar_texto,
    validar_numero_telefono,
    detectar_sql_injection,
    rate_limiter,
    log_intento_sql_injection,
    log_login_fallido,
    log_login_exitoso,
    obtener_ip_cliente,
    validar_longitud
)
# ==========================================

app = Flask(__name__)
app.secret_key = 'kinderfiesta_secret_key_2025'
CORS(app)
# ========== CREDENCIALES DE ADMINISTRADOR ==========
ADMIN_EMAIL = "admin@kinderfiesta.com"
ADMIN_PASSWORD = "123" 
# ==================================================


# Configuración
UPLOAD_FOLDER = 'static/solicitudes'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/solicitudes', exist_ok=True)


ADMIN_EMAIL = 'admin@kinderfiesta.com'


PALABRAS_PROHIBIDAS = [
    'aborto', 'abortar', 'asno', 'bastardo', 'baboso', 'bobo', 'boludo', 'borracho', 'bruto', 'burro',
    'cabrón', 'cabronazo', 'caca', 'cagada', 'cagado', 'cagón', 'cagar', 'cago', 'calienta huevos', 'carajo',
    'cerdo', 'chupapijas', 'chupamedias', 'chupapolla', 'chupa', 'chúpame', 'chingada', 'chingado', 'chingar', 'chingón',
    'cholo', 'chota', 'choto', 'cochina', 'cochino', 'cojón', 'cojones', 'cojudazo', 'cojudo', 'coludo',
    'conchatumadre', 'concha', 'conchudo', 'cornudo', 'córrete', 'cretino', 'culo', 'culiado', 'culicagado', 'culón',
    'culona', 'culero', 'cursi', 'desgraciado', 'diablos', 'estúpido', 'estúpida', 'feo', 'forro', 'gil',
    'gilipollas', 'gorra', 'grosero', 'grone', 'groncho', 'guarango', 'guevón', 'guevona', 'guevazos', 'hijo de puta',
    'hijoputa', 'hijueputa', 'hijueputas', 'idiota', 'imbécil', 'imbecil', 'infeliz', 'jilipollas', 'jodido', 'joder', 'joto',
    'loco de mierda', 'lameculos', 'lamemierda', 'lamehuevos', 'lamebotas', 'leproso', 'lerdo', 'mala leche', 'malnacido', 'maldito',
    'maldita', 'malparido', 'mamón', 'mamada', 'mamar', 'marica', 'maricón', 'maricona', 'mariconazo', 'mariposón',
    'mierda', 'mierdoso', 'mongólico', 'mongolo', 'mocoso', 'muerto de hambre', 'naco', 'nalgón', 'ojete', 'ojón',
    'pajero', 'pajillero', 'pajote', 'pajuo', 'pajuato', 'pelotudo', 'pendejo', 'pendeja', 'pendejada', 'pendejazo',
    'pene', 'perra', 'perro', 'petardo', 'pezuñas', 'picha', 'pichulón', 'pinche', 'pinga', 'piruja',
    'pirobo', 'pitera', 'pito', 'plasta', 'plomo', 'puta', 'puto', 'putazo', 'putilla', 'putón',
    'putona', 'putear', 'putearse', 'putísima', 'putísimo', 'putañero', 'putañera', 'putero', 'polla', 'pollazo',
    'pichacorta', 'prostituta', 'prostituto', 'rata', 'ratero', 'retrasado', 'ridículo', 'sabandija', 'salame', 'sapazo',
    'sapenco', 'sapo', 'shit', 'sidoso', 'sorete', 'subnormal', 'tarado', 'teta', 'tetona', 'tetón',
    'tontazo', 'tonto', 'tonteja', 'tontillo', 'torpe', 'travesti', 'triplehijueputa', 'triplehijoputa', 'trolo', 'trola',
    'troll', 'vaca', 'vagabunda', 'vagabundo', 'vale verga', 'vergazo', 'verguita', 'verga', 'vergon', 'vergonazo',
    'vieja de mierda', 'viejo pendejo', 'zorra', 'zorrón', 'zorrónazo', 'zángano'
]


def filtrar_palabras(texto):
    palabras = texto.split()
    texto_filtrado = []
    for palabra in palabras:
        palabra_lower = palabra.lower()
        censurada = False
        for prohibida in PALABRAS_PROHIBIDAS:
            if prohibida in palabra_lower:
                texto_filtrado.append('*' * len(palabra))
                censurada = True
                break
        if not censurada:
            texto_filtrado.append(palabra)
    return ' '.join(texto_filtrado)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============ RUTAS PÚBLICAS ============


@app.route('/')
def index():
    """Página de inicio con estadísticas dinámicas"""
    try:
        # Obtener estadísticas de la base de datos
        stats = db.obtener_estadisticas()
        
        print(f"📊 Estadísticas: Familias={stats['familias']}, Salones={stats['salones']}, Satisfacción={stats['satisfaccion']}%")
        
        return render_template('index.html', stats=stats)
    except Exception as e:
        print(f"❌ Error al cargar inicio: {e}")
        # Valores por defecto si hay error
        stats = {
            'familias': 1,
            'salones': 5,
            'tiempo_respuesta': '24h'
        }
        return render_template('index.html', stats=stats)


@app.route('/salones')
def salones_page():
    """Página de Salones"""
    try:
        stats = db.obtener_estadisticas()
        return render_template('salones.html', stats=stats)
    except Exception as e:
        print(f"❌ Error al cargar salones: {e}")
        stats = {
            'familias': 1,
            'salones': 5,
            'tiempo_respuesta': '24h'
        }
        return render_template('salones.html', stats=stats)

@app.route('/buscar', methods=['GET'])
def buscar_salon():
    """Buscar salones por nombre o ubicación"""
    try:
        # Obtener el término de búsqueda
        query = request.args.get('q', '').strip()
        
        print(f"🔍 Búsqueda realizada: '{query}'")
        
        # Si no hay término, redirigir a todos los salones
        if not query:
            return redirect(url_for('salones'))
        
        # Buscar en la base de datos
        salones = db.buscar_salones(query)
        
        if salones:
            print(f"✅ Se encontraron {len(salones)} salones")
            return render_template('buscar_resultados.html', query=query, salones=salones)
        else:
            print(f"❌ No se encontraron salones para: {query}")
            return render_template('buscar_resultados.html', query=query, salones=[])
    
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return redirect(url_for('salones'))

@app.route('/salon/<int:salon_id>')
def detalle_salon(salon_id):
    """Página de detalle de un salón específico"""
    try:
        # Obtener datos del salón
        salon = db.obtener_salon_por_id(salon_id)
        
        if not salon:
            flash('Salón no encontrado', 'error')
            return redirect(url_for('salones'))
        
        print(f"✅ Mostrando detalles del salón: {salon.get('nombre', 'Sin nombre')}")
        
        # Obtener horarios
        horarios = db.obtener_horarios_salon(salon_id)
        
        # Renderizar página de detalle
        return render_template('salon_detalle.html', 
                             salon=salon,
                             horarios=horarios)
        
    except Exception as e:
        print(f"❌ Error al cargar salón: {e}")
        flash('Error al cargar el salón', 'error')
        return redirect(url_for('salones'))
    
@app.route('/nosotros')
def nosotros_page():
    """Página de Nosotros"""
    try:
        stats = db.obtener_estadisticas()
        return render_template('nosotros.html', stats=stats)
    except Exception as e:
        print(f"❌ Error al cargar nosotros: {e}")
        stats = {
            'familias': 1,
            'salones': 5,
            'tiempo_respuesta': '24h'
        }
        return render_template('nosotros.html', stats=stats)


@app.route('/contacto')
def contacto_page():
    """Página de Contacto"""
    try:
        stats = db.obtener_estadisticas()
        return render_template('contacto.html', stats=stats)
    except Exception as e:
        print(f"❌ Error al cargar contacto: {e}")
        stats = {
            'familias': 1,
            'salones': 5,
            'tiempo_respuesta': '24h'
        }
        return render_template('contacto.html', stats=stats)


@app.route('/registrar-local', methods=['GET'])
def registrar_local_page():
    """Página para registrar un nuevo local"""
    return render_template('registrar_local.html')

@app.route('/api/salones')
def get_salones():
    """API pública - Solo salones visibles con TODAS las fotos (5 imágenes)"""
    try:
        # ✅ CONSULTA SQL DIRECTA PARA OBTENER EL CAMPO 'fotos'
        conn = db.conectar()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.id, s.name, s.phone, s.address, s.locationCode, 
                   s.category, s.rating, s.visible, s.folder, s.fotos
            FROM salones s
            WHERE s.visible = 1
            ORDER BY s.rating DESC, s.name ASC
        """)
        
        salones = cursor.fetchall()
        
        # Procesar cada salón para incluir sus reviews
        for salon in salones:
            salon_id = salon['id']
            
            # ✅ Si no tiene fotos definidas, usar valores por defecto (5 fotos)
            if not salon['fotos']:
                salon['fotos'] = '1.jpg, 2.jpg, 3.jpg, 4.jpg, 5.jpg'
            
            # Si no tiene rating, asignar 0
            if salon['rating'] is None:
                salon['rating'] = 0.0
            
            # Obtener reviews del salón
            cursor.execute("""
                SELECT id, nombre, comentario, rating, fecha
                FROM reviews
                WHERE salon_id = %s
                ORDER BY fecha DESC
            """, (salon_id,))
            
            reviews = cursor.fetchall()
            
            # Convertir datetime a string para JSON
            for review in reviews:
                review['fecha'] = review['fecha'].isoformat()
            
            salon['reviews'] = reviews
        
        cursor.close()
        conn.close()
        
        print(f"✅ API /salones: {len(salones)} salones retornados con fotos completas")
        return jsonify(salones)
        
    except Exception as e:
        print(f"❌ Error en /api/salones: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas reales y coherentes"""
    try:
        # 1. Contar salones verificados
        salones = db.obtener_todos_salones()
        total_salones = len([s for s in salones if s.get('visible', 1) == 1])
        
        # 2. Contar usuarios registrados (familias conectadas)
        try:
            conn = db.conectar()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as total FROM usuarios WHERE activo = 1")
            resultado = cursor.fetchone()
            total_usuarios = resultado['total'] if resultado else 0
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error al contar usuarios: {e}")
            total_usuarios = 0
        
        # 3. Calcular satisfacción (promedio de estrellas de testimonios)
        try:
            conn = db.conectar()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT AVG(rating) as promedio FROM testimonios WHERE aprobado = 1")
            resultado = cursor.fetchone()
            promedio_rating = resultado['promedio'] if resultado and resultado['promedio'] else 0
            satisfaccion = int((promedio_rating / 5) * 100) if promedio_rating > 0 else 98
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error al calcular satisfacción: {e}")
            satisfaccion = 98
        
        print(f"✅ Stats: {total_usuarios} usuarios, {total_salones} salones, {satisfaccion}% satisfacción")
        
        return jsonify({
            'familias': f"{total_usuarios}+" if total_usuarios > 0 else "0",
            'salones': f"{total_salones}+",
            'satisfaccion': f"{satisfaccion}%",
            'tiempo': '24h'
        })
    except Exception as e:
        print(f"❌ Error en /api/stats: {str(e)}")
        return jsonify({
            'familias': '0',
            'salones': '0+',
            'satisfaccion': '98%',
            'tiempo': '24h'
        }), 500


# ============ RUTAS DE USUARIOS Y TESTIMONIOS ============


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuarios con protección anti SQL Injection"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        ip_address = obtener_ip_cliente(request)
        
        print(f"🔐 Intento de login - IP: {ip_address}, Email: {email}")
        
        # 1. VERIFICAR RATE LIMITING
        permitido, tiempo_restante = rate_limiter.verificar_intento(ip_address)
        if not permitido:
            log_login_fallido(ip_address, email, f'Bloqueado por {tiempo_restante} minutos')
            return render_template('login.html', 
                error=f'Demasiados intentos fallidos. Intenta en {tiempo_restante} minutos.')
        
        # 2. VALIDAR EMAIL
        if not validar_email(email):
            rate_limiter.registrar_intento(ip_address)
            log_login_fallido(ip_address, email, 'Email inválido')
            print(f"❌ Email inválido: {email}")
            return render_template('login.html', error='Email inválido')
        
        # 3. DETECTAR SQL INJECTION
        if detectar_sql_injection(email) or detectar_sql_injection(password):
            log_intento_sql_injection(ip_address, '/login', {
                'email': email,
                'password': '***'
            })
            rate_limiter.registrar_intento(ip_address)
            print(f"🚨 SQL Injection detectado - IP: {ip_address}")
            return render_template('login.html', 
                error='Datos inválidos. El intento ha sido registrado.')
        
        # 4. VALIDAR LONGITUD
        if not validar_longitud(password, 6, 100):
            rate_limiter.registrar_intento(ip_address)
            log_login_fallido(ip_address, email, 'Contraseña con longitud inválida')
            return render_template('login.html', error='Contraseña inválida')
        
        # 5. VERIFICAR CREDENCIALES
        usuario = db.verificar_login(email, password)
        
        if usuario and isinstance(usuario, dict):  # ← VERIFICACIÓN IMPORTANTE
            session['user_logged_in'] = True
            session['user_id'] = usuario.get('id')
            session['user_nombre'] = usuario.get('nombre')
            session['user_email'] = usuario.get('email')
            
            rate_limiter.limpiar_intentos(ip_address)
            log_login_exitoso(ip_address, email, 'usuario')
            
            print(f"✅ Login exitoso: {email}")
            return redirect(url_for('index'))
        else:
            rate_limiter.registrar_intento(ip_address)
            log_login_fallido(ip_address, email)
            return render_template('login.html', error='Email o contraseña incorrectos')
    
    return render_template('login.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro_page():
    """Página de registro"""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        password2 = request.form.get('password2', '').strip()
        
        if not nombre or not email or not password:
            return render_template('registro.html', error='Todos los campos son requeridos')
        
        if len(nombre) < 3:
            return render_template('registro.html', error='El nombre debe tener al menos 3 caracteres')
        
        if len(password) < 6:
            return render_template('registro.html', error='La contraseña debe tener al menos 6 caracteres')
        
        if password != password2:
            return render_template('registro.html', error='Las contraseñas no coinciden')
        
        user_id, mensaje = db.registrar_usuario(nombre, email, password)
        
        if user_id:
            session['user_logged_in'] = True
            session['user_id'] = user_id
            session['user_nombre'] = nombre
            session['user_email'] = email
            session['mostrar_modal_testimonio'] = True
            return redirect(url_for('index'))
        else:
            return render_template('registro.html', error=mensaje)
    
    return render_template('registro.html')


@app.route('/logout')
def logout_user():
    """Cerrar sesión de usuario"""
    session.pop('user_logged_in', None)
    session.pop('user_id', None)
    session.pop('user_nombre', None)
    session.pop('user_email', None)
    return redirect(url_for('index'))


@app.route('/api/testimonios')
def api_testimonios():
    """API: Obtener testimonios aprobados"""
    try:
        testimonios = db.obtener_testimonios_aprobados(limite=10)
        
        print(f"✅ API /api/testimonios: Enviando {len(testimonios)} testimonios")
        return jsonify(testimonios)
        
    except Exception as e:
        print(f"❌ Error en API /api/testimonios: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500



@app.route('/api/agregar-testimonio', methods=['POST'])
def agregar_testimonio_route():
    """Agregar testimonio de usuario"""
    if not session.get('user_logged_in'):
        return jsonify({'success': False, 'message': 'Debes iniciar sesión para dejar un testimonio'}), 401
    
    try:
        data = request.json
        rating = data.get('rating')
        comentario = data.get('comentario', '').strip()
        
        if not rating or not comentario:
            return jsonify({'success': False, 'message': 'Rating y comentario son requeridos'}), 400
        
        if rating < 1 or rating > 5:
            return jsonify({'success': False, 'message': 'El rating debe estar entre 1 y 5'}), 400
        
        if len(comentario) > 500:
            return jsonify({'success': False, 'message': 'El comentario no puede superar los 500 caracteres'}), 400
        
        # Verificar si ya comentó
        if db.verificar_usuario_ya_comento(session['user_id']):
            return jsonify({'success': False, 'message': 'Ya has dejado un testimonio anteriormente'}), 400
        
        # Filtrar malas palabras
        comentario_filtrado = filtrar_palabras(comentario)
        
        # Agregar testimonio
        testimonio_id, mensaje = db.agregar_testimonio(
            session['user_id'],
            session['user_nombre'],
            rating,
            comentario_filtrado
        )
        
        if testimonio_id:
            return jsonify({'success': True, 'message': 'Testimonio agregado exitosamente'})
        else:
            return jsonify({'success': False, 'message': mensaje}), 500
        
    except Exception as e:
        print(f"❌ Error al agregar testimonio: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/limpiar-modal-testimonio', methods=['POST'])
def limpiar_modal_testimonio():
    """Limpiar la bandera de modal de testimonio después de mostrarlo"""
    session.pop('mostrar_modal_testimonio', None)
    return jsonify({'success': True})


# ============ RUTAS PARA SALONES Y COMENTARIOS ============


@app.route('/api/salon/<int:salon_id>')
def get_salon(salon_id):
    """Obtener salón específico con todas sus fotos"""
    try:
        conn = db.conectar()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT s.id, s.name, s.phone, s.address, s.locationCode, 
                   s.category, s.rating, s.visible, s.folder, s.fotos
            FROM salones s
            WHERE s.id = %s AND s.visible = 1
        """, (salon_id,))
        
        salon = cursor.fetchone()
        
        if salon:
            # Si no tiene fotos, usar valores por defecto
            if not salon['fotos']:
                salon['fotos'] = '1.jpg, 2.jpg, 3.jpg, 4.jpg, 5.jpg'
            
            if salon['rating'] is None:
                salon['rating'] = 0.0
            
            # Obtener reviews
            cursor.execute("""
                SELECT id, nombre, comentario, rating, fecha
                FROM reviews
                WHERE salon_id = %s
                ORDER BY fecha DESC
            """, (salon_id,))
            
            reviews = cursor.fetchall()
            
            for review in reviews:
                review['fecha'] = review['fecha'].isoformat()
            
            salon['reviews'] = reviews
            
            cursor.close()
            conn.close()
            
            print(f"✅ Salón obtenido: {salon['name']}")
            return jsonify(salon)
        
        cursor.close()
        conn.close()
        
        print(f"❌ Salón no encontrado o no visible: {salon_id}")
        return jsonify({'error': 'Salón no encontrado'}), 404
        
    except Exception as e:
        print(f"❌ Error en /api/salon/{salon_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/comentario', methods=['POST'])
def agregar_comentario():
    """Agregar comentario a un salón"""
    try:
        data = request.json
        salon_id = data.get('salon_id')
        nombre = data.get('nombre', '').strip()
        comentario = data.get('comentario', '').strip()
        rating = data.get('rating')

        if not nombre or not comentario or not rating:
            return jsonify({'error': 'Todos los campos son requeridos'}), 400
        if len(comentario) > 500:
            return jsonify({'error': 'El comentario no puede superar los 500 caracteres'}), 400
        if rating < 1 or rating > 5:
            return jsonify({'error': 'La calificación debe estar entre 1 y 5'}), 400

        comentario_filtrado = filtrar_palabras(comentario)
        review, nuevo_rating = db.agregar_review(salon_id, nombre, comentario_filtrado, rating)
        
        if review:
            print(f"✅ Comentario agregado al salón {salon_id}")
            return jsonify({'success': True, 'review': review, 'nuevo_rating': nuevo_rating})
        else:
            return jsonify({'error': 'No se pudo agregar el comentario'}), 500
    except Exception as e:
        print(f"❌ Error al agregar comentario: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/registrar-local', methods=['POST'])
def registrar_local():
    """Registrar nuevo local (crear solicitud)"""
    try:
        nombre = request.form.get('nombre', '').strip()
        categoria = request.form.get('categoria', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        direccion = request.form.get('direccion', '').strip()
        zona = request.form.get('zona', '').strip()
        telefono = request.form.get('telefono', '').strip()
        whatsapp = request.form.get('whatsapp', '').strip()
        email = request.form.get('email', '').strip()
        google_maps = request.form.get('google_maps', '').strip()
        horarios = json.loads(request.form.get('horarios', '[]'))  # ← Cambiar '{}' por '[]'
        servicios = json.loads(request.form.get('servicios', '[]'))
        
        if not nombre or not direccion or not telefono:
            return jsonify({'success': False, 'message': 'Los campos Nombre, Dirección y Teléfono son obligatorios'}), 400
        
        nombre = filtrar_palabras(nombre)
        descripcion = filtrar_palabras(descripcion)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        solicitud_id = f"solicitud_{timestamp}"
        
        fotos_folder = os.path.join(UPLOAD_FOLDER, solicitud_id)
        os.makedirs(fotos_folder, exist_ok=True)
        
        fotos_guardadas = []
        if 'fotos' in request.files:
            fotos = request.files.getlist('fotos')
            
            if len(fotos) < 3:
                return jsonify({'success': False, 'message': 'Debes subir al menos 3 fotos de tu local'}), 400
            
            if len(fotos) > 5:
                return jsonify({'success': False, 'message': 'Máximo 5 fotos permitidas'}), 400
            
            for i, foto in enumerate(fotos, 1):
                if foto and allowed_file(foto.filename):
                    filename = f"{i}.jpg"
                    filepath = os.path.join(fotos_folder, filename)
                    foto.save(filepath)
                    fotos_guardadas.append(filename)
                else:
                    return jsonify({'success': False, 'message': f'Formato de imagen no válido. Solo se permiten: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        else:
            return jsonify({'success': False, 'message': 'Debes subir fotos de tu local'}), 400
        
        solicitud = {
            'id': solicitud_id,
            'fecha_solicitud': datetime.now().isoformat(),
            'estado': 'pendiente',
            'datos': {
                'nombre': nombre,
                'categoria': categoria,
                'descripcion': descripcion,
                'direccion': direccion,
                'zona': zona,
                'telefono': telefono,
                'whatsapp': whatsapp,
                'email': email,
                'google_maps': google_maps,
                'horarios': horarios,
                'servicios': servicios,
                'fotos': fotos_guardadas,
                'carpeta_fotos': solicitud_id
            }
        }
        
        solicitudes_file = 'data/solicitudes/solicitudes.json'
        
        if os.path.exists(solicitudes_file):
            with open(solicitudes_file, 'r', encoding='utf-8') as f:
                try:
                    solicitudes = json.load(f)
                except json.JSONDecodeError:
                    solicitudes = []
        else:
            solicitudes = []
        
        solicitudes.append(solicitud)
        
        with open(solicitudes_file, 'w', encoding='utf-8') as f:
            json.dump(solicitudes, f, indent=4, ensure_ascii=False)
        
        print(f"✅ Nueva solicitud registrada: {solicitud_id}")
        
        return jsonify({'success': True, 'message': 'Solicitud enviada correctamente. Un administrador la revisará pronto.', 'solicitud_id': solicitud_id})
        
    except Exception as e:
        print(f"❌ Error al procesar solicitud: {str(e)}")
        return jsonify({'success': False, 'message': f'Error al procesar la solicitud: {str(e)}'}), 500


# ============ RUTAS DE ADMINISTRACIÓN ============


@app.route('/admin')
def admin_redirect():
    """Redirige a login o dashboard según sesión"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Login de administrador con protección anti SQL Injection"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        ip_address = obtener_ip_cliente(request)
        
        print(f"👑 Intento de login ADMIN - IP: {ip_address}, Email: {email}")
        
        # 1. VERIFICAR RATE LIMITING (más estricto para admin)
        permitido, tiempo_restante = rate_limiter.verificar_intento(ip_address, max_intentos=3, ventana_minutos=10)
        if not permitido:
            log_login_fallido(ip_address, email, f'Admin bloqueado por {tiempo_restante} minutos')
            print(f"🚫 BLOQUEADO POR RATE LIMIT: {tiempo_restante} minutos")
            return render_template('admin_login.html', 
                error=f'Demasiados intentos fallidos. Intenta en {tiempo_restante} minutos.')
        
        # 2. VALIDAR EMAIL
        if not validar_email(email):
            rate_limiter.registrar_intento(ip_address)
            log_login_fallido(ip_address, email, 'Admin - Email inválido')
            print(f"❌ Admin - Email inválido: {email}")
            return render_template('admin_login.html', error='Email inválido')
        
        # 3. DETECTAR SQL INJECTION
        if detectar_sql_injection(email) or detectar_sql_injection(password):
            log_intento_sql_injection(ip_address, '/admin/login', {
                'email': email,
                'password': '***',
                'tipo': 'ADMIN LOGIN'
            })
            rate_limiter.registrar_intento(ip_address)
            print(f"🚨🚨 SQL Injection en ADMIN LOGIN - IP: {ip_address}")
            return render_template('admin_login.html', 
                error='Intento de acceso sospechoso detectado y registrado.')
        
        # 4. VERIFICAR CREDENCIALES ADMIN
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_email'] = email
            
            rate_limiter.limpiar_intentos(ip_address)
            log_login_exitoso(ip_address, email, 'ADMIN')
            
            print(f"✅ Admin login exitoso: {email}")
            return redirect(url_for('admin_dashboard'))
        else:
            rate_limiter.registrar_intento(ip_address)
            log_login_fallido(ip_address, email, 'Admin - Credenciales incorrectas')
            print(f"❌ Admin - Credenciales incorrectas")
            return render_template('admin_login.html', error='Credenciales incorrectas')
    
    return render_template('admin_login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    """Dashboard principal del administrador"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        salones = db.obtener_todos_salones()
        total_salones = len(salones)
        salones_visibles = len([s for s in salones if s.get('visible', 1) == 1])
        salones_ocultos = total_salones - salones_visibles
        
        total_reviews = sum(len(s.get('reviews', [])) for s in salones)
        
        try:
            solicitudes_file = 'data/solicitudes/solicitudes.json'
            if os.path.exists(solicitudes_file):
                with open(solicitudes_file, 'r', encoding='utf-8') as f:
                    solicitudes = json.load(f)
                solicitudes_pendientes = len([s for s in solicitudes if s['estado'] == 'pendiente'])
            else:
                solicitudes_pendientes = 0
        except:
            solicitudes_pendientes = 0
        
        stats = {
            'total_salones': total_salones,
            'salones_visibles': salones_visibles,
            'salones_ocultos': salones_ocultos,
            'total_reviews': total_reviews,
            'solicitudes_pendientes': solicitudes_pendientes
        }
        
        print(f"✅ Dashboard stats: {stats}")
        return render_template('admin_dashboard.html', stats=stats)
    except Exception as e:
        print(f"❌ Error en dashboard: {str(e)}")
        return render_template('admin_dashboard.html', stats={'total_salones': 0, 'salones_visibles': 0, 'salones_ocultos': 0, 'total_reviews': 0, 'solicitudes_pendientes': 0})


@app.route('/admin/panel')
def admin_panel():
    """Panel de gestión de salones"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    try:
        salones = db.obtener_todos_salones()
        
        # Formatear datos para el panel
        salones_fmt = []
        for salon in salones:
            salon_fmt = {
                'id': salon.get('id') or salon.get('salon_id'),
                'name': salon.get('nombre') or salon.get('name') or 'Sin nombre',
                'category': salon.get('categoria') or salon.get('category') or 'Salón',
                'address': salon.get('direccion') or salon.get('address') or 'Sin dirección',
                'phone': salon.get('telefono') or salon.get('phone') or 'N/A',
                'rating': salon.get('promedio') or salon.get('rating') or 0,
                'visible': salon.get('visible', 1),
                'reviews': salon.get('reviews') or [],
                'folder': salon.get('carpeta_fotos') or salon.get('folder') or f"salon{salon.get('id')}"
            }
            salones_fmt.append(salon_fmt)
        
        print(f"✅ Panel: {len(salones_fmt)} salones cargados")
        return render_template('admin_panel.html', salones=salones_fmt)
    except Exception as e:
        print(f"❌ Error en admin_panel: {str(e)}")
        return render_template('admin_panel.html', salones=[])
    
@app.route('/admin/solicitudes')
def admin_solicitudes():
    """Página de solicitudes pendientes"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    return render_template('admin_solicitudes.html')

@app.route('/admin/logout')
def admin_logout():
    """Cerrar sesión"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))


@app.route('/api/admin/solicitudes', methods=['GET'])
def obtener_solicitudes():
    """Obtener solicitudes pendientes"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        solicitudes_file = 'data/solicitudes/solicitudes.json'
        
        if os.path.exists(solicitudes_file):
            with open(solicitudes_file, 'r', encoding='utf-8') as f:
                solicitudes = json.load(f)
        else:
            solicitudes = []
        
        print(f"✅ Solicitudes: {len(solicitudes)} encontradas")
        return jsonify(solicitudes)
        
    except Exception as e:
        print(f"❌ Error al obtener solicitudes: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/solicitud/<solicitud_id>/aprobar', methods=['POST'])
def aprobar_solicitud(solicitud_id):
    """Aprobar solicitud"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        solicitudes_file = 'data/solicitudes/solicitudes.json'
        
        with open(solicitudes_file, 'r', encoding='utf-8') as f:
            solicitudes = json.load(f)
        
        solicitud = next((s for s in solicitudes if s['id'] == solicitud_id), None)
        
        if not solicitud:
            return jsonify({'success': False, 'message': 'Solicitud no encontrada'}), 404
        
        carpeta_fotos = solicitud['datos'].get('carpeta_fotos', solicitud_id)
        salon_id = db.agregar_salon_desde_solicitud(solicitud['datos'], carpeta_fotos)
        
        if salon_id:
            origen = os.path.join('static/solicitudes', carpeta_fotos)
            destino = os.path.join('static/imagenes', carpeta_fotos)
            
            try:
                if os.path.exists(origen):
                    os.makedirs('static/imagenes', exist_ok=True)
                    if os.path.exists(destino):
                        shutil.rmtree(destino)
                    shutil.copytree(origen, destino)
                    print(f"✅ Fotos movidas a: {destino}")
            except Exception as e:
                print(f"⚠️ Error al mover fotos: {e}")
            
            solicitud['estado'] = 'aprobado'
            solicitud['fecha_aprobacion'] = datetime.now().isoformat()
            solicitud['salon_id'] = salon_id
            
            with open(solicitudes_file, 'w', encoding='utf-8') as f:
                json.dump(solicitudes, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Solicitud aprobada: {solicitud_id} -> Salón ID: {salon_id}")
            
            return jsonify({'success': True, 'message': f'Solicitud aprobada. Salón creado con ID: {salon_id}', 'salon_id': salon_id})
        else:
            return jsonify({'success': False, 'message': 'Error al crear el salón en la base de datos'}), 500
        
    except Exception as e:
        print(f"❌ Error al aprobar solicitud: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/solicitud/<solicitud_id>/rechazar', methods=['POST'])
def rechazar_solicitud(solicitud_id):
    """Rechazar solicitud"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        solicitudes_file = 'data/solicitudes/solicitudes.json'
        
        with open(solicitudes_file, 'r', encoding='utf-8') as f:
            solicitudes = json.load(f)
        
        solicitud = next((s for s in solicitudes if s['id'] == solicitud_id), None)
        
        if not solicitud:
            return jsonify({'success': False, 'message': 'Solicitud no encontrada'}), 404
        
        solicitud['estado'] = 'rechazado'
        solicitud['fecha_rechazo'] = datetime.now().isoformat()
        motivo = request.json.get('motivo', 'No especificado') if request.is_json else 'No especificado'
        solicitud['motivo_rechazo'] = motivo
        
        with open(solicitudes_file, 'w', encoding='utf-8') as f:
            json.dump(solicitudes, f, indent=4, ensure_ascii=False)
        
        print(f"❌ Solicitud rechazada: {solicitud_id}")
        
        return jsonify({'success': True, 'message': 'Solicitud rechazada'})
        
    except Exception as e:
        print(f"❌ Error al rechazar solicitud: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/comentario/<int:salon_id>/<int:review_id>', methods=['DELETE'])
def eliminar_comentario(salon_id, review_id):
    """Eliminar comentario"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401

    if db.eliminar_review(salon_id, review_id):
        nuevo_promedio = db.recalcular_promedio_salon(salon_id)
        print(f"✅ Comentario eliminado de salón {salon_id}")
        return jsonify({'success': True, 'nuevo_promedio': nuevo_promedio})
    else:
        return jsonify({'error': 'No se pudo eliminar el comentario'}), 500


@app.route('/api/admin/comentario/<int:salon_id>/<int:review_id>', methods=['PUT'])
def editar_comentario(salon_id, review_id):
    """Editar comentario"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401

    data = request.json
    nuevo_nombre = data.get('nombre', '').strip()
    nuevo_comentario = data.get('comentario', '').strip()
    nuevo_rating = data.get('rating')

    if not nuevo_nombre or not nuevo_comentario or not nuevo_rating:
        return jsonify({'error': 'Todos los campos son obligatorios'}), 400
    if len(nuevo_comentario) > 500:
        return jsonify({'error': 'El comentario no puede superar los 500 caracteres'}), 400
    if nuevo_rating < 1 or nuevo_rating > 5:
        return jsonify({'error': 'El rating debe estar entre 1 y 5'}), 400

    nuevo_comentario = filtrar_palabras(nuevo_comentario)
    nuevo_nombre = filtrar_palabras(nuevo_nombre)
    
    review = db.actualizar_review(salon_id, review_id, nuevo_comentario, nuevo_rating, nuevo_nombre)

    if review:
        print(f"✅ Comentario actualizado en salón {salon_id}")
        return jsonify({'success': True, 'review': review})
    else:
        return jsonify({'error': 'No se pudo actualizar el comentario'}), 500


@app.route('/api/admin/salon/<int:salon_id>/visibilidad', methods=['PUT'])
def cambiar_visibilidad(salon_id):
    """Cambiar visibilidad del salón"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        data = request.json
        visible = data.get('visible', True)
        
        if db.cambiar_visibilidad_salon(salon_id, visible):
            estado = "visible" if visible else "oculto"
            print(f"✅ Salón {salon_id} ahora está {estado}")
            return jsonify({'success': True, 'message': f'El salón ahora está {estado}', 'visible': visible})
        else:
            return jsonify({'success': False, 'message': 'No se pudo cambiar la visibilidad'}), 500
    except Exception as e:
        print(f"❌ Error al cambiar visibilidad: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/salon/<int:salon_id>', methods=['DELETE'])
def eliminar_salon_route(salon_id):
    """Eliminar salón"""
    if not session.get('admin_logged_in'):
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        if db.eliminar_salon(salon_id):
            print(f"✅ Salón {salon_id} eliminado")
            return jsonify({'success': True, 'message': 'El salón fue eliminado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'No se pudo eliminar el salón'}), 500
    except Exception as e:
        print(f"❌ Error al eliminar salón: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
# ============================================
# RUTAS API (para JavaScript)
# ============================================

@app.route('/api/salones')
def api_salones():
    """API: Obtener todos los salones visibles"""
    try:
        salones = db.obtener_todos_salones()
        
        # Filtrar solo salones visibles
        salones_visibles = [s for s in salones if s.get('visible', 0) == 1]
        
        # Formatear para JavaScript
        resultados = []
        for salon in salones_visibles:
            resultados.append({
                'id': salon['id'],
                'name': salon.get('nombre', salon.get('name', 'Sin nombre')),
                'address': salon.get('direccion', salon.get('address', 'Sin dirección')),
                'category': salon.get('categoria', salon.get('category', 'Salón Infantil')),
                'rating': float(salon.get('promedio', salon.get('rating', 0))),
                'folder': salon.get('carpeta_fotos', salon.get('folder', f"salon{salon['id']}")),
            })
        
        print(f"✅ API: Enviando {len(resultados)} salones")
        return jsonify(resultados)
        
    except Exception as e:
        print(f"❌ Error en API salones: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([]), 500


@app.route('/api/stats')
def api_stats():
    """API: Obtener estadísticas para la página de inicio"""
    try:
        stats = db.obtener_estadisticas()
        
        print(f"✅ API: Enviando estadísticas - Familias: {stats['familias']}, Salones: {stats['salones']}")
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Error en API stats: {e}")
        # Valores por defecto si hay error
        return jsonify({
            'familias': 1,
            'salones': 5,
            'satisfaccion': 98,
            'tiempo_respuesta': '24h'
        })

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 INICIANDO KINDERFIESTA")
    print("=" * 60)
    if db.test_connection():
        print("✅ Base de datos conectada correctamente")
        print("📁 Carpetas de solicitudes creadas")
        print("=" * 60)
        print("🌐 Servidor corriendo en http://127.0.0.1:5000")
        print("=" * 60 + "\n")
        app.run(debug=True, port=5000)
    else:
        print("❌ Error: No se pudo conectar a la base de datos")
        print("Verifica tu configuración en database.py")
        print("=" * 60 + "\n")
