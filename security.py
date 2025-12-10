"""
security.py - Módulo de Seguridad para KinderFiesta
Implementa medidas contra SQL Injection y otros ataques
Autor: [Tu nombre]
Fecha: 19 de Noviembre 2025
"""

import re
import html
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================
# 1. VALIDACIÓN Y SANITIZACIÓN DE ENTRADAS
# ============================================

def validar_email(email):
    """
    Valida formato de email y previene inyección SQL
    
    Args:
        email (str): Email a validar
        
    Returns:
        bool: True si es válido, False si es peligroso
    """
    if not email or len(email) > 100:
        return False
    
    # Patrón seguro para emails
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(patron, email):
        return False
    
    # Verificar caracteres peligrosos
    caracteres_peligrosos = ["'", '"', '--', ';', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
    email_upper = email.upper()
    
    for peligro in caracteres_peligrosos:
        if peligro in email_upper:
            return False
    
    return True


def sanitizar_texto(texto, max_length=500):
    """
    Sanitiza texto eliminando caracteres peligrosos
    Previene SQL Injection y XSS
    
    Args:
        texto (str): Texto a sanitizar
        max_length (int): Longitud máxima permitida
        
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    # Limitar longitud
    texto = str(texto)[:max_length]
    
    # Escapar HTML (previene XSS)
    texto = html.escape(texto)
    
    # Remover caracteres peligrosos para SQL
    caracteres_peligrosos = [
        '--',  # Comentarios SQL
        ';--', # Inyección con comentarios
        '/*',  # Comentarios de bloque
        '*/',
        'xp_',  # Procedimientos extendidos
        'sp_',  # Procedimientos almacenados
    ]
    
    for peligro in caracteres_peligrosos:
        texto = texto.replace(peligro, '')
    
    return texto.strip()


def validar_numero_telefono(telefono):
    """
    Valida que el teléfono solo contenga números y caracteres seguros
    
    Args:
        telefono (str): Número de teléfono
        
    Returns:
        bool: True si es válido
    """
    if not telefono:
        return False
    
    # Solo permitir números, espacios, guiones y paréntesis
    patron = r'^[\d\s\-\(\)]+$'
    
    if not re.match(patron, telefono):
        return False
    
    # Verificar longitud razonable (5-20 caracteres)
    telefono_limpio = re.sub(r'[\s\-\(\)]', '', telefono)
    if len(telefono_limpio) < 5 or len(telefono_limpio) > 20:
        return False
    
    return True


def detectar_sql_injection(texto):
    """
    Detecta patrones comunes de SQL Injection
    
    Args:
        texto (str): Texto a analizar
        
    Returns:
        bool: True si se detecta un ataque, False si es seguro
    """
    if not texto:
        return False
    
    texto_upper = str(texto).upper()
    
    # Patrones comunes de SQL Injection
    patrones_peligrosos = [
        r"('\s*(OR|AND)\s*'?\d*'?\s*=\s*'?\d*)",  # ' OR '1'='1
        r"(--|\#|\/\*)",  # Comentarios SQL
        r"(UNION\s+SELECT)",  # UNION-based injection
        r"(DROP\s+TABLE)",  # Drop table
        r"(INSERT\s+INTO)",  # Insert injection
        r"(DELETE\s+FROM)",  # Delete injection
        r"(UPDATE\s+\w+\s+SET)",  # Update injection
        r"(EXEC\s*\()",  # Ejecución de comandos
        r"(EXECUTE\s+IMMEDIATE)",  # Oracle injection
        r"(WAITFOR\s+DELAY)",  # Time-based blind injection
        r"(BENCHMARK\s*\()",  # MySQL benchmark
        r"(SLEEP\s*\()",  # MySQL sleep
        r"(xp_cmdshell)",  # SQL Server command shell
        r"(;\s*SHUTDOWN)",  # Shutdown database
    ]
    
    for patron in patrones_peligrosos:
        if re.search(patron, texto_upper, re.IGNORECASE):
            return True
    
    return False


# ============================================
# 2. RATE LIMITING (Prevenir Fuerza Bruta)
# ============================================

class RateLimiter:
    """
    Limita el número de intentos de login por IP
    Previene ataques de fuerza bruta
    """
    def __init__(self):
        self.intentos = defaultdict(list)
        self.bloqueados = {}
    
    def verificar_intento(self, ip_address, max_intentos=5, ventana_minutos=15):
        """
        Verifica si una IP puede intentar login
        
        Args:
            ip_address (str): Dirección IP
            max_intentos (int): Máximo de intentos permitidos
            ventana_minutos (int): Ventana de tiempo en minutos
            
        Returns:
            tuple: (permitido: bool, tiempo_restante: int)
        """
        ahora = datetime.now()
        
        # Verificar si está bloqueado
        if ip_address in self.bloqueados:
            tiempo_bloqueo = self.bloqueados[ip_address]
            if ahora < tiempo_bloqueo:
                tiempo_restante = (tiempo_bloqueo - ahora).seconds // 60
                return False, tiempo_restante
            else:
                # Desbloquear
                del self.bloqueados[ip_address]
        
        # Limpiar intentos antiguos
        ventana = timedelta(minutes=ventana_minutos)
        self.intentos[ip_address] = [
            t for t in self.intentos[ip_address]
            if ahora - t < ventana
        ]
        
        # Verificar número de intentos
        if len(self.intentos[ip_address]) >= max_intentos:
            # Bloquear por 30 minutos
            self.bloqueados[ip_address] = ahora + timedelta(minutes=30)
            return False, 30
        
        return True, 0
    
    def registrar_intento(self, ip_address):
        """Registra un intento fallido de login"""
        self.intentos[ip_address].append(datetime.now())
    
    def limpiar_intentos(self, ip_address):
        """Limpia los intentos después de un login exitoso"""
        if ip_address in self.intentos:
            del self.intentos[ip_address]


# Instancia global del rate limiter
rate_limiter = RateLimiter()


# ============================================
# 3. LOGGING DE SEGURIDAD
# ============================================

def log_intento_sql_injection(ip_address, endpoint, datos):
    """
    Registra intentos de SQL Injection
    
    Args:
        ip_address (str): IP del atacante
        endpoint (str): Ruta atacada
        datos (dict): Datos del intento
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open('security_logs.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] ⚠️ INTENTO DE SQL INJECTION DETECTADO\n")
            f.write(f"IP: {ip_address}\n")
            f.write(f"Endpoint: {endpoint}\n")
            f.write(f"Datos: {datos}\n")
            f.write(f"{'='*80}\n")
        
        print(f"🚨 [SECURITY] SQL Injection detectado desde {ip_address}")
    except Exception as e:
        print(f"Error al escribir log: {e}")


def log_login_fallido(ip_address, email, razon='Credenciales incorrectas'):
    """
    Registra intentos de login fallidos
    
    Args:
        ip_address (str): IP del usuario
        email (str): Email usado
        razon (str): Razón del fallo
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open('security_logs.txt', 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] ❌ Login fallido - IP: {ip_address} - Email: {email} - Razón: {razon}\n")
    except Exception as e:
        print(f"Error al escribir log: {e}")


def log_login_exitoso(ip_address, email, tipo_usuario='usuario'):
    """
    Registra logins exitosos
    
    Args:
        ip_address (str): IP del usuario
        email (str): Email usado
        tipo_usuario (str): Tipo de usuario (usuario/ADMIN)
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        with open('security_logs.txt', 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] ✅ Login exitoso - IP: {ip_address} - Email: {email} - Tipo: {tipo_usuario}\n")
    except Exception as e:
        print(f"Error al escribir log: {e}")


# ============================================
# 4. FUNCIONES DE UTILIDAD
# ============================================

def obtener_ip_cliente(request):
    """
    Obtiene la IP real del cliente, considerando proxies
    
    Args:
        request: Objeto request de Flask
        
    Returns:
        str: Dirección IP del cliente
    """
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    
    return ip


def validar_longitud(texto, min_len=1, max_len=500):
    """
    Valida que el texto tenga longitud adecuada
    
    Args:
        texto (str): Texto a validar
        min_len (int): Longitud mínima
        max_len (int): Longitud máxima
        
    Returns:
        bool: True si cumple con la longitud
    """
    if not texto:
        return min_len == 0
    
    longitud = len(str(texto))
    return min_len <= longitud <= max_len


# ============================================
# 5. PRUEBAS Y VALIDACIÓN
# ============================================

if __name__ == "__main__":
    """
    Pruebas básicas del módulo de seguridad
    Ejecutar: python security.py
    """
    print("🔒 Módulo de Seguridad - KinderFiesta")
    print("="*50)
    
    # Prueba 1: Validación de emails
    print("\n📧 PRUEBA 1: Validación de Emails")
    emails_prueba = [
        ("admin@test.com", True),
        ("admin@test.com' OR '1'='1", False),
        ("test@example.com; DROP TABLE--", False),
        ("usuario.valido@domain.es", True),
    ]
    
    for email, esperado in emails_prueba:
        resultado = validar_email(email)
        emoji = "✅" if resultado == esperado else "❌"
        print(f"  {emoji} {email[:40]:40} → {resultado}")
    
    # Prueba 2: Detección de SQL Injection
    print("\n🛡️ PRUEBA 2: Detección de SQL Injection")
    payloads_prueba = [
        ("texto normal", False),
        ("' OR '1'='1", True),
        ("'; DROP TABLE usuarios--", True),
        ("' UNION SELECT password--", True),
        ("admin' AND SLEEP(5)--", True),
    ]
    
    for payload, esperado in payloads_prueba:
        resultado = detectar_sql_injection(payload)
        emoji = "✅" if resultado == esperado else "❌"
        print(f"  {emoji} {payload[:40]:40} → {'BLOQUEADO' if resultado else 'SEGURO'}")
    
    print("\n" + "="*50)
    print("✅ Módulo de seguridad funcionando correctamente")
