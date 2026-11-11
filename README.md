# Rentis

Sistema web de arriendo y control de herramientas para el caso BuildCorp de la Evaluación 3 de Desarrollo Backend.

- **Estudiante:** Rayen Alejandra Calfin Melivilu
- **Sección:** AP_N4_C1
- **Tecnologías:** Python, Django, Django REST Framework, PostgreSQL y Django Templates.

## Ejecución local

1. Abre la carpeta donde está `manage.py` y activa tu entorno virtual.
2. Instala las dependencias del proyecto:

   ```bash
   python -m pip install -r requirements.txt
   ```

3. Para una instalación nueva, crea una base de datos en PostgreSQL y copia `.env.example` como `.env` junto a `manage.py`. Configura la conexión a PostgreSQL y la clave secreta de Django. Si ya tienes una instalación de Rentis, puedes conservar tu `.env` local. Mantén ese archivo fuera del repositorio.
4. Aplica las migraciones, revisa la configuración e inicia el servidor:

   ```bash
   python manage.py migrate
   python manage.py check
   python manage.py runserver
   ```

5. Abre [Rentis](http://127.0.0.1:8000/). Puedes crear una cuenta de cliente desde **Iniciar sesión → Crear cuenta**. Para gestionar el inventario, inicia sesión con una cuenta de rol **Administrador** y abre **Mi panel**.

## Funcionalidades

- **Cuentas y permisos.** Registro de clientes, inicio y cierre de sesión, y acceso según el rol de cliente, trabajador o administrador.
- **Inventario.** Creación y edición de categorías, herramientas, ubicaciones y unidades físicas desde el panel de Rentis. Permite crear varias unidades desde una sola ficha, asignarles códigos únicos correlativos y buscarlas por nombre o código en un listado paginado.
- **Trazabilidad.** Historial de cambios manuales de estado y ubicación por unidad. Las unidades dadas de baja conservan su historial.
- **Catálogo y carrito.** Catálogo público con búsqueda y filtro por categoría. El carrito se conserva al cerrar sesión y la disponibilidad se valida para las fechas seleccionadas al solicitar el arriendo.
- **Solicitudes.** El personal puede aprobar o rechazar solicitudes. El cliente puede cancelar una solicitud propia antes de la entrega, según su estado.
- **Entrega y devolución.** Registro del responsable de obra, firma dibujada e historial de movimientos. El sistema registra el cargo por daño y calcula el reembolso por devolución anticipada para gestión manual.
- **Mantenimiento y atrasos.** Mantenimiento preventivo por fecha u horas de uso. Avisos de devoluciones atrasadas y bloqueo de nuevas solicitudes mientras exista un atraso pendiente.
- **Administración.** Panel propio con templates para gestionar inventario, usuarios y solicitudes, y consultar reportes de unidades, arriendos y atrasos.
- **Página 404.** Pantalla personalizada con un botón para volver al inicio. Se muestra con `DJANGO_DEBUG=False`.

## API y documentación técnica

| Método y ruta | Uso |
|---|---|
| `GET /api/catalogo/` | Consulta pública del catálogo. |
| `POST /api/token/` | Recibe `username` y `password` para obtener los tokens JWT de acceso y renovación. |
| `POST /api/token/refresh/` | Recibe `refresh` para obtener un nuevo token de acceso. |
| `GET /api/perfil/` | Consulta el perfil con el encabezado `Authorization: Bearer <access>`. |

Las pantallas web usan sesiones de Django. Swagger (`/api/swagger/`) y ReDoc (`/api/redoc/`) se abren por URL directa con una sesión de administrador.

## Evidencia de uso de IA

Las consultas y el apoyo recibido durante el desarrollo se registran en [prompts_ia.md](prompts_ia.md).

## Despliegue

- **Ejecución local:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Dirección pública de AWS EC2:** [http://100.31.232.248/](http://100.31.232.248/) (IP elástica).
- **Instancia:** `Rentis-EC2`, región `us-east-1` (Norte de Virginia).
- **Arquitectura:** Django y PostgreSQL 16 en la misma instancia EC2, con Gunicorn y Nginx.