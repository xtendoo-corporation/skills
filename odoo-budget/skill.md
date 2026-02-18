Objetivo: construir el caso completo y verificar desviaciones.

Pasos en Browser (con capturas):

Login en {{odoo.url}}/web con usuario/clave.

Ir a Contabilidad → Configuración → Ajustes y confirmar que están activos:

Contabilidad analítica

Presupuestos / Budget Management

Crear Proyecto:

Proyecto → Proyectos → Nuevo

Nombre: {{case.project.name}}

Vincular/crear Cuenta analítica {{case.project.analytic_account}}

Screenshot del formulario guardado.

Crear/validar Posiciones presupuestarias (si no existen):

Contabilidad → Configuración → Posiciones presupuestarias

Crear las 4 posiciones del YAML y vincularlas a sus cuentas contables.

Screenshot de la lista.

Crear Presupuesto:

Contabilidad → Presupuestos → Presupuestos → Nuevo

Nombre + periodo + líneas:

cada línea con Posición, Cuenta analítica {{case.project.analytic_account}} e Importe planificado

Confirmar/activar presupuesto.

Screenshot del presupuesto con líneas.

Crear Facturas de cliente (ingresos):

Contabilidad → Clientes → Facturas → Nuevo

Cargar líneas y asignar Distribución analítica 100% a {{case.project.analytic_account}}

Publicar.

Repetir para las 3.

Screenshot de una factura publicada mostrando la distribución analítica.

Crear Facturas de proveedor (gastos):

Contabilidad → Proveedores → Facturas → Nuevo

Asignar Distribución analítica al proyecto.

Publicar las 3.

Screenshot de una factura publicada.

Ver desviaciones del presupuesto:

Abrir el presupuesto y revisar columnas Planificado vs Real (y %/desviación)

Screenshot donde se vea claramente:

Subcontratación con sobrecoste

Licencias con sobrecoste

Viajes con ahorro

Artefacto final:

Tabla-resumen: plan vs real por línea + desviación y margen.