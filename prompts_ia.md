# Registro de apoyo de IA

- «Necesito que hagamos esto rápido ya que lo tengo que entregar mañana». La IA revisó el ZIP del proyecto y la pauta, priorizó el inventario y generó formularios, vistas protegidas, rutas y templates.
- «Dame la solución para estos 2 errores que te envié». La IA detectó problemas de sangría en los modelos del inventario y corrigió la ubicación de la función que genera el código y la clase UnidadFisica.
- «Necesito que al equivocarse de contraseña o al poner el mismo usuario me mande un mensaje en rojo». La IA preparó los estilos para los mensajes de validación de Django y ayudó a verificar la carga del CSS.

- «Sí funciona mi inventario al iniciar sesión como admin, sigamos con lo que falta». Se incorporaron el carrito persistente, la validación de fechas y las solicitudes de arriendo.

- «Sí funciona, sigamos». Se implementó el registro de entrega y devolución con confirmación nominal, cambio de estado y cargo por daño.

- «Ya ahora sí funcionó, sigamos». Se agruparon mantenimiento preventivo, bloqueo por atrasos y cálculo de reembolso.

- Se incorporó historial de inventario, JWT para DRF, Swagger, ReDoc, gestión de cuentas y reportes.
## Cambios posteriores a la versión inicial

| Consulta a la IA | Apoyo recibido |
|---|---|
| Incorporar una firma dibujada en entregas y devoluciones. | Se propuso la captura en pantalla, la validación con Pillow y el guardado de la firma en el historial. |
| Agregar aprobación, rechazo y cancelación de solicitudes. | Se definieron los estados, permisos y reglas para liberar reservas. La prueba de nueva reserva después de rechazar sigue pendiente. |
| Crear varias unidades físicas desde una ficha de herramienta. | Se propuso generar códigos correlativos, como MA-01 y MA-02, al registrar o aumentar la cantidad. |
| Buscar una unidad por nombre o código. | Se agregó una búsqueda con paginación de 10 unidades. |
| Corregir errores al registrar una herramienta. | Se corrigió el uso de la transacción y se inicializaron las variables del historial. |
| Personalizar el error 404. | Se preparó una pantalla propia con un botón para volver al inicio. |