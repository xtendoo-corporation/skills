# Skill: Odoo Provisioner (DB bootstrap vía YAML)

## Propósito

Provisionar una base de datos de Odoo a partir de un fichero `provision.yml` con intervención mínima:

- Idiomas: activar idioma principal y extra
- Compañía: crear/actualizar datos (nombre, VAT, dirección, logo)
- Usuarios iniciales (opcional)
- Instalar módulos (lista declarativa)
- Configuración de correo saliente y aliases
- Parámetros `ir.config_parameter`
- Validación final en navegador + evidencias (capturas)

## Cuándo usar esta skill

Úsala cuando el usuario pida:

- "Configurar una DB desde cero"
- "Crear empresa, idiomas, mail y módulos automáticamente"
- "Repetir la misma puesta en marcha en muchas bases de datos"
- "Provisioning / bootstrap / plantilla de base de datos"

## Entradas requeridas

- Ruta al YAML: `provision.yml` (o una ruta equivalente)
- Acceso a la URL de Odoo y credenciales de admin (idealmente por variables de entorno)
- Entorno con Python 3 disponible para ejecutar scripts

## Reglas / Guardarraíles

- NO borrar bases de datos.
- Si la DB existe, operar en modo idempotente:
  - crear lo que falte
  - actualizar lo que sea seguro (campos de compañía, smtp, parámetros)
  - NO tocar moneda si ya hay apuntes / contabilidad activa (si detectas riesgo, aborta con aviso).
- NO instalar/desinstalar módulos fuera de la lista.
- Si falla un paso, parar y dejar:
  - diagnóstico claro
  - comando exacto para reintentar
  - logs y evidencias si están disponibles

## Estrategia general

1. Validar entrada `provision.yml` (schema mínimo y variables requeridas)
2. Conectar a Odoo por API (XML-RPC) y verificar autenticación
3. Activar idiomas y timezone
4. Crear/actualizar compañía principal
5. Instalar módulos (por lotes)
6. Crear/actualizar SMTP y probar envío
7. Aplicar `ir.config_parameter`
8. (Opcional) crear usuarios iniciales
9. Validación final:
   - por API (rápida)
   - por Browser (visual) + screenshots

---

## Implementación recomendada (scripts)

Esta skill asume una carpeta `tools/odoo_provisioner/` con:

- `provision.py` -> ejecuta todo (idempotente)
- `requirements.txt` -> dependencias (pyyaml, requests opcional)
- `README.md` -> cómo ejecutar manualmente

### Dependencias

- Python 3
- pip
- Librerías: pyyaml

---

## Comandos estándar (Terminal)

> Ejecutar siempre desde la raíz del repo.

### 0) Preparación

- Exportar secretos antes de ejecutar:
  - `export ODOO_ADMIN_PASSWORD="..."`
  - `export SMTP_PASSWORD="..."`

### 1) Ejecutar provisioning

```bash
python3 tools/odoo_provisioner/provision.py --config provision.yml
```
