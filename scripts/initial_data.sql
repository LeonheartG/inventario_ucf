-- scripts/initial_data.sql
-- Datos iniciales para el sistema UCF

-- Insertar departamentos básicos
INSERT OR IGNORE INTO usuarios_departamento (nombre, descripcion, ubicacion) VALUES
('General', 'Departamento general para usuarios sin asignación específica', 'Campus Principal'),
('Tecnologías de la Información', 'Departamento de TI y soporte técnico', 'Edificio Administrativo'),
('Administración', 'Departamento administrativo y financiero', 'Edificio Administrativo'),
('Ingeniería', 'Facultad de Ingeniería', 'Edificio de Ingeniería'),
('Ciencias Económicas', 'Facultad de Ciencias Económicas', 'Edificio de Economía'),
('Ciencias Sociales', 'Facultad de Ciencias Sociales', 'Edificio de Humanidades'),
('Rectoría', 'Rectoría y administración central', 'Edificio Rector'),
('Biblioteca', 'Sistema de bibliotecas universitarias', 'Biblioteca Central');

-- Insertar roles del sistema
INSERT OR IGNORE INTO usuarios_rol (nombre, descripcion, permisos) VALUES
('Superadministrador', 'Acceso completo a todo el sistema, incluyendo configuración y administración de usuarios.', 'ALL'),
('Administrador', 'Acceso completo a inventario, reportes y gestión de departamento.', 'INVENTARIO,REPORTES,USUARIOS,LOCALES,DIAGNOSTICO'),
('Supervisor', 'Acceso a reportes, visualización completa de inventario y diagnósticos.', 'INVENTARIO_READ,REPORTES,LOCALES_READ,DIAGNOSTICO'),
('Coordinador', 'Acceso a gestión de su departamento y reportes básicos.', 'INVENTARIO_DEPT,REPORTES_BASIC,LOCALES_DEPT,DIAGNOSTICO_DEPT'),
('Técnico', 'Acceso a gestión de inventario y mantenimientos.', 'INVENTARIO,MANTENIMIENTO,LOCALES_READ'),
('Analista', 'Acceso a reportes y análisis de datos.', 'REPORTES,INVENTARIO_READ,DIAGNOSTICO_READ'),
('Usuario Regular', 'Acceso básico de consulta a inventario y diagnósticos.', 'INVENTARIO_READ,DIAGNOSTICO_BASIC');

-- Crear usuario administrador por defecto (solo si no existe)
-- Nota: Este script debe ejecutarse después de las migraciones
/*
INSERT OR IGNORE INTO auth_user (username, first_name, last_name, email, is_staff, is_active, is_superuser, date_joined, password)
VALUES (
    'admin',
    'Administrador',
    'del Sistema',
    'admin@ucf.edu.cu',
    1,
    1,
    1,
    datetime('now'),
    'pbkdf2_sha256$260000$admin123$hashedpassword'  -- Cambiar por hash real
);
*/