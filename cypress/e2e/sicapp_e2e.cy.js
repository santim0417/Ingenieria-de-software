/**
 * Suite de Pruebas de Sistema (E2E) y Aceptacion BDD (Gherkin: Dado - Cuando - Entonces)
 * Proyecto: SICAPP_PROTOTIPO (Flask: http://127.0.0.1:5000)
 * Equipo QA: Maria Yazmin Giraldo Salazar (Test Lead) & Santiago Moreno Sarmiento (QA Analyst)
 */

describe('Suite E2E y Aceptacion BDD - SICAPP Prototipo (Jira: SIC)', () => {

  const BASE_URL = 'http://127.0.0.1:5000';

  // =========================================================================
  // HISTORIA DE USUARIO: SIC-2 | HU-01 - Login Seguro (RF-1 - RNF3)
  // =========================================================================
  context('SIC-2 (HU-01): Login Seguro, Limites BVA y Bloqueo por Intentos', () => {

    it('TC-SIC2-01 (BVA): Rechazo de contrasena menor al limite inferior (< 8 caracteres)', () => {
      // DADO que el usuario se encuentra en la pantalla de inicio de sesion de SICAPP
      cy.visit(`${BASE_URL}/login`);

      // CUANDO ingresa un correo institucional valido pero una clave de solo 7 caracteres
      cy.get('input[name="email"]').type('maria.giraldo663@pascualbravo.edu.co');
      cy.get('input[name="password"]').type('Pass123');
      cy.get('button.btn-ingresar').click();

      // ENTONCES el sistema muestra alerta indicando el minimo de 8 caracteres
      cy.get('.alert-danger')
        .should('be.visible')
        .and('contain', 'Error: La contraseña debe contener al menos 8 caracteres.');
    });

    it('TC-SIC2-03 (BVA): Rechazo de contrasena mayor al limite superior (> 16 caracteres)', () => {
      // DADO que el usuario se encuentra en la pantalla de inicio de sesion de SICAPP
      cy.visit(`${BASE_URL}/login`);

      // CUANDO ingresa una contrasena de 17 caracteres que supera el limite permitido
      cy.get('input[name="email"]').type('maria.giraldo663@pascualbravo.edu.co');
      cy.get('input[name="password"]').type('Password123456789');
      cy.get('button.btn-ingresar').click();

      // ENTONCES el sistema muestra alerta indicando que no puede superar los 16 caracteres
      cy.get('.alert-danger')
        .should('be.visible')
        .and('contain', 'Error: La contraseña no puede superar los 16 caracteres.');
    });

    it('TC-SIC8-02: Validacion de formato de correo electronico invalido', () => {
      // DADO que el usuario abre el formulario de login de SICAPP
      cy.visit(`${BASE_URL}/login`);

      // CUANDO ingresa un texto sin estructura de correo electronico valido
      cy.get('input[name="email"]').type('correo_invalido_sin_arroba');
      cy.get('input[name="password"]').type('Password123');
      cy.get('button.btn-ingresar').click();

      // ENTONCES el sistema impide el acceso y notifica formato de correo no valido
      cy.get('.alert-danger')
        .should('be.visible')
        .and('contain', 'Error: Formato de correo electrónico no válido');
    });

    it('TC-SIC2-04: Login exitoso de Estudiante y navegacion a modulos permitidos', () => {
      // DADO que la estudiante Maria Yazmin ingresa a la vista de Login
      cy.visit(`${BASE_URL}/login`);

      // CUANDO ingresa sus credenciales validas (Password123 - 11 caracteres)
      cy.get('input[name="email"]').type('maria.giraldo663@pascualbravo.edu.co');
      cy.get('input[name="password"]').type('Password123');
      cy.get('button.btn-ingresar').click();

      // ENTONCES accede a /home, visualiza su bienvenida y puede navegar al Modulo de Estudiantes
      cy.url().should('include', '/home');
      cy.contains('Hola MARIA, ¡Bienvenid@ a SICAPP!').should('be.visible');
      cy.contains('a', 'Estudiantes').click();
      cy.url().should('include', '/estudiantes');
      cy.contains('1037498663 CC').should('be.visible');
    });
  });

  // =========================================================================
  // HISTORIA DE USUARIO: SIC-11 | HU-05 - Estructura de Roles y RBAC (RF-3 - RNF3)
  // =========================================================================
  context('SIC-11 (HU-05): Control de Acceso Basado en Roles (RBAC) en /gestion-notas', () => {

    it('TC-SIC11-01: Bloqueo HTTP 403 Forbidden para rol ESTUDIANTE en /gestion-notas', () => {
      // DADO que un usuario con rol ESTUDIANTE ha iniciado sesion en SICAPP
      cy.visit(`${BASE_URL}/login`);
      cy.get('input[name="email"]').type('maria.giraldo663@pascualbravo.edu.co');
      cy.get('input[name="password"]').type('Password123');
      cy.get('button.btn-ingresar').click();

      // CUANDO intenta acceder directamente al endpoint protegido /gestion-notas
      cy.visit(`${BASE_URL}/gestion-notas`, { failOnStatusCode: false });

      // ENTONCES el sistema bloquea el acceso y renderiza la pantalla 403 Forbidden (TC-SIC11-01)
      cy.contains('SICAPP - HTTP 403 Forbidden').should('be.visible');
      cy.contains('Acceso Denegado (TC-SIC11-01)').should('be.visible');
      cy.contains('posee el rol ESTUDIANTE').should('be.visible');
    });

    it('TC-SIC11-02: Acceso exitoso HTTP 200 OK para rol DOCENTE en /gestion-notas', () => {
      // DADO que el docente Santiago Moreno inicia sesion con credenciales validas
      cy.visit(`${BASE_URL}/login`);
      cy.get('input[name="email"]').type('santiago.moreno@pascualbravo.edu.co');
      cy.get('input[name="password"]').type('DocentePass1');
      cy.get('button.btn-ingresar').click();

      // CUANDO navega hacia el modulo protegido /gestion-notas
      cy.visit(`${BASE_URL}/gestion-notas`);

      // ENTONCES el sistema valida su rol DOCENTE y concede acceso HTTP 200 OK (TC-SIC11-02)
      cy.contains('SICAPP - HTTP 200 OK (Gestión de Notas)').should('be.visible');
      cy.contains('Bienvenido Profe SANTIAGO MORENO SARMIENTO').should('be.visible');
      cy.contains('TC-SIC11-02').should('be.visible');
    });
  });

  // =========================================================================
  // HISTORIA DE USUARIO: SIC-26 | HU-03 - Notificaciones Push y Cierre de Sesion
  // =========================================================================
  context('SIC-26 (HU-03): Desvinculacion de Token Push al Cerrar Sesion', () => {

    it('TC-SIC26-02: Cierre de sesion exitoso y desvinculacion de Token Push', () => {
      // DADO que el usuario tiene una sesion activa con token Push asignado
      cy.visit(`${BASE_URL}/login`);
      cy.get('input[name="email"]').type('santiago.moreno@pascualbravo.edu.co');
      cy.get('input[name="password"]').type('DocentePass1');
      cy.get('button.btn-ingresar').click();

      // CUANDO hace clic en el enlace Cerrar sesion en la barra superior
      cy.contains('a', 'Cerrar sesión').click();

      // ENTONCES redirige a /login y confirma que el Token Push fue desvinculado
      cy.url().should('include', '/login');
      cy.get('.alert-info')
        .should('be.visible')
        .and('contain', 'Sesión cerrada. Token Push desvinculado correctamente.');
    });
  });

});
