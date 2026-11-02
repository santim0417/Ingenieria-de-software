import unittest
import os
import sys

# Asegura que importe app.py tanto si se ejecuta dentro de SICAPP_PROTOTIPO como desde la carpeta raiz
if os.path.exists(os.path.join(os.path.dirname(__file__), 'SICAPP_PROTOTIPO')):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'SICAPP_PROTOTIPO')))

from app import app, es_correo_valido, USUARIOS_DB

class TestSicappQA(unittest.TestCase):
    """
    Suite de Pruebas Unitarias y de Integracion para SICAPP_PROTOTIPO (Flask)
    Autores: Maria Yazmin Giraldo Salazar (Test Lead) & Santiago Moreno Sarmiento (QA Analyst)
    """

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'clave_secreta_sicapp_qa'
        self.client = app.test_client()
        # Restaurar estado limpio de la BD sintetica antes de cada caso (Seeding QA - TC-SIC9-01)
        USUARIOS_DB["maria.giraldo663@pascualbravo.edu.co"]["intentos_fallidos"] = 0
        USUARIOS_DB["maria.giraldo663@pascualbravo.edu.co"]["bloqueado"] = False
        USUARIOS_DB["santiago.moreno@pascualbravo.edu.co"]["intentos_fallidos"] = 0
        USUARIOS_DB["santiago.moreno@pascualbravo.edu.co"]["bloqueado"] = False

    # =========================================================================
    # NIVEL 1: PRUEBAS UNITARIAS PURAS (Funciones y Seeding QA)
    # =========================================================================

    def test_01_tc_sic9_01_seeding_usuarios_db(self):
        """TC-SIC9-01: Verificar integridad del Seeding QA en USUARIOS_DB (Estudiante y Docente)"""
        self.assertIn("maria.giraldo663@pascualbravo.edu.co", USUARIOS_DB)
        self.assertIn("santiago.moreno@pascualbravo.edu.co", USUARIOS_DB)
        self.assertEqual(USUARIOS_DB["maria.giraldo663@pascualbravo.edu.co"]["rol"], "ESTUDIANTE")
        self.assertEqual(USUARIOS_DB["santiago.moreno@pascualbravo.edu.co"]["rol"], "DOCENTE")
        self.assertEqual(USUARIOS_DB["maria.giraldo663@pascualbravo.edu.co"]["documento"], "1037498663 CC")
        self.assertEqual(USUARIOS_DB["santiago.moreno@pascualbravo.edu.co"]["documento"], "1098765432 CC")

    def test_02_tc_sic8_02_unit_validador_correo_institucional(self):
        """TC-SIC8-02 (Unitaria): Validar funcion es_correo_valido() con formatos validos e invalidos"""
        self.assertTrue(es_correo_valido("maria.giraldo663@pascualbravo.edu.co"))
        self.assertTrue(es_correo_valido("santiago.moreno@pascualbravo.edu.co"))
        self.assertFalse(es_correo_valido("correo_sin_arroba.com"))
        self.assertFalse(es_correo_valido("usuario@dominio_sin_extension"))
        self.assertFalse(es_correo_valido(""))

    # =========================================================================
    # NIVEL 2: PRUEBAS DE INTEGRACION / FUNCIONALES (Rutas Flask y Reglas BVA)
    # =========================================================================

    def test_03_tc_sic2_01_bva_password_menor_a_8_caracteres(self):
        """TC-SIC2-01 (BVA): Rechazar contrasena con menos de 8 caracteres (7 chars)"""
        response = self.client.post('/login', data={
            'email': 'maria.giraldo663@pascualbravo.edu.co',
            'password': 'Pass123'  # 7 caracteres (Limite inferior invalido)
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: La contraseña debe contener al menos 8 caracteres.", response.get_data(as_text=True))

    def test_04_tc_sic2_03_bva_password_mayor_a_16_caracteres(self):
        """TC-SIC2-03 (BVA): Rechazar contrasena con mas de 16 caracteres (17 chars)"""
        response = self.client.post('/login', data={
            'email': 'maria.giraldo663@pascualbravo.edu.co',
            'password': 'Password123456789'  # 17 caracteres (Limite superior invalido)
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: La contraseña no puede superar los 16 caracteres.", response.get_data(as_text=True))

    def test_05_tc_sic8_02_formato_correo_invalido_en_login(self):
        """TC-SIC8-02 (Integracion): Validar alerta cuando se envia email con formato invalido en /login"""
        response = self.client.post('/login', data={
            'email': 'maria.giraldo663_invalido',
            'password': 'Password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Error: Formato de correo electrónico no válido", response.get_data(as_text=True))

    def test_06_tc_sic2_04_login_exitoso_y_token_push(self):
        """TC-SIC2-04 y TC-SIC26-01: Login exitoso (8-16 chars) y registro de device_token_push en sesion"""
        response = self.client.post('/login', data={
            'email': 'maria.giraldo663@pascualbravo.edu.co',
            'password': 'Password123'  # 11 caracteres (Valida: 8-16)
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("¡Bienvenid@ a SICAPP!", response.get_data(as_text=True))
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['usuario']['rol'], 'ESTUDIANTE')
            self.assertEqual(sess['device_token_push'], 'FCM_TOKEN_SIMULATED_2026_XYZ')

    def test_07_tc_sic2_05_y_06_bloqueo_cuenta_3_intentos_fallidos(self):
        """TC-SIC2-05 y TC-SIC2-06: Bloqueo temporal de cuenta al 3er intento fallido consecutivo y alerta"""
        email = 'maria.giraldo663@pascualbravo.edu.co'
        # Intento 1 fallido
        r1 = self.client.post('/login', data={'email': email, 'password': 'WrongPassword1'})
        self.assertIn("Te quedan 2 intento(s).", r1.get_data(as_text=True))
        # Intento 2 fallido
        r2 = self.client.post('/login', data={'email': email, 'password': 'WrongPassword2'})
        self.assertIn("Te quedan 1 intento(s).", r2.get_data(as_text=True))
        # Intento 3 fallido -> Activa bloqueo (TC-SIC2-05)
        r3 = self.client.post('/login', data={'email': email, 'password': 'WrongPassword3'})
        self.assertIn("Cuenta Bloqueada temporalmente al 3er intento fallido consecutivo.", r3.get_data(as_text=True))
        self.assertTrue(USUARIOS_DB[email]['bloqueado'])
        # Intento 4 con clave correcta pero cuenta ya bloqueada (TC-SIC2-06)
        r4 = self.client.post('/login', data={'email': email, 'password': 'Password123'})
        self.assertIn("Alerta de seguridad emitida.", r4.get_data(as_text=True))

    def test_08_tc_sic11_01_rbac_403_estudiante_en_gestion_notas(self):
        """TC-SIC11-01 (RBAC): Estudiante recibe HTTP 403 Forbidden al intentar acceder a /gestion-notas"""
        self.client.post('/login', data={
            'email': 'maria.giraldo663@pascualbravo.edu.co',
            'password': 'Password123'
        })
        response = self.client.get('/gestion-notas')
        self.assertEqual(response.status_code, 403)
        self.assertIn("SICAPP - HTTP 403 Forbidden", response.get_data(as_text=True))
        self.assertIn("Acceso Denegado (TC-SIC11-01)", response.get_data(as_text=True))

    def test_09_tc_sic11_02_rbac_200_docente_en_gestion_notas(self):
        """TC-SIC11-02 (RBAC): Docente accede con HTTP 200 OK al endpoint protegido /gestion-notas"""
        self.client.post('/login', data={
            'email': 'santiago.moreno@pascualbravo.edu.co',
            'password': 'DocentePass1'
        })
        response = self.client.get('/gestion-notas')
        self.assertEqual(response.status_code, 200)
        self.assertIn("SICAPP - HTTP 200 OK (Gestión de Notas)", response.get_data(as_text=True))
        self.assertIn("TC-SIC11-02", response.get_data(as_text=True))

    def test_10_tc_sic26_02_logout_desvincula_token_push(self):
        """TC-SIC26-02: Cerrar sesion elimina la sesion activa y desvincula el Token Push"""
        self.client.post('/login', data={
            'email': 'santiago.moreno@pascualbravo.edu.co',
            'password': 'DocentePass1'
        })
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Sesión cerrada. Token Push desvinculado correctamente.", response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main(verbosity=2)
