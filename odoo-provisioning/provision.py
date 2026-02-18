import argparse
import os
import sys
import time
import socket
import logging
import yaml
import xmlrpc.client
from typing import Any, Dict, List, Optional, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("odoo_provision")

# Set socket timeout to prevent indefinite hangs (e.g., 5 minutes)
socket.setdefaulttimeout(300)

MAX_RETRIES = 3
RETRY_DELAY = 5


def die(msg: str, code: int = 2):
    logger.error(msg)
    sys.exit(code)


def load_config(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        die(f"No existe el fichero de configuración: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return cfg


def env_expand(value: Any) -> Any:
    # Expande strings del tipo "${VAR}"
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        var = value[2:-1]
        v = os.getenv(var)
        if v is None:
            die(f"Falta variable de entorno requerida: {var}")
        return v
    return value


def deep_env_expand(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: deep_env_expand(env_expand(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_env_expand(env_expand(v)) for v in obj]
    return env_expand(obj)


import ssl


def xmlrpc_connect(base_url: str, db: str, login: str, password: str):
    logger.info(f"Conectando a {base_url} (db={db})...")
    try:
        # Create unverified SSL context to avoid certificate errors
        context = ssl._create_unverified_context()
        common = xmlrpc.client.ServerProxy(
            f"{base_url}/xmlrpc/2/common", context=context
        )
        uid = common.authenticate(db, login, password, {})
        if not uid:
            die("Autenticación fallida. Revisa db/admin_login/admin_password.")
        models = xmlrpc.client.ServerProxy(
            f"{base_url}/xmlrpc/2/object", context=context
        )
        return uid, models
    except Exception as e:
        die(f"Error de conexión XML-RPC: {e}")


def model_exec(
    models, db: str, uid: int, password: str, model: str, method: str, *args, **kwargs
):
    """
    Ejecuta una llamada XML-RPC con reintentos para fallos transitorios.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            return models.execute_kw(db, uid, password, model, method, args, kwargs)
        except (socket.timeout, ConnectionError, xmlrpc.client.ProtocolError) as e:
            attempt += 1
            logger.warning(
                f"Error en {model}.{method} (intento {attempt}/{MAX_RETRIES}): {e}"
            )
            if attempt >= MAX_RETRIES:
                die(
                    f"Fallo permanente tras {MAX_RETRIES} intentos en {model}.{method}: {e}"
                )
            time.sleep(RETRY_DELAY)
        except xmlrpc.client.Fault as e:
            # Errores de lógica de Odoo no se deben reintentar ciegamente, pero logueamos
            logger.error(
                f"Odoo Fault en {model}.{method}: {e.faultCode} - {e.faultString}"
            )
            raise e
        except Exception as e:
            logger.error(f"Excepción inesperada en {model}.{method}: {e}")
            raise e


def ensure_company(models, db, uid, password, company_data: Dict[str, Any]):
    logger.info("Verificando configuración de compañía...")
    # Buscar compañía principal (limit=1)
    ids = model_exec(models, db, uid, password, "res.company", "search", [], limit=1)
    if not ids:
        logger.warning("No se encontró ninguna compañía para actualizar.")
        return

    vals = {
        "name": company_data.get("name"),
        "vat": company_data.get("vat"),
        "email": company_data.get("email"),
        "phone": company_data.get("phone"),
        "website": company_data.get("website"),
        "street": company_data.get("street"),
        "zip": company_data.get("zip"),
        "city": company_data.get("city"),
    }
    # Country
    country_code = company_data.get("country_code")
    if country_code:
        c_ids = model_exec(
            models,
            db,
            uid,
            password,
            "res.country",
            "search",
            [("code", "=", country_code)],
            limit=1,
        )
        if c_ids:
            vals["country_id"] = c_ids[0]
            # State
            state_name = company_data.get("state")
            if state_name:
                s_ids = model_exec(
                    models,
                    db,
                    uid,
                    password,
                    "res.country.state",
                    "search",
                    [
                        ("country_id", "=", c_ids[0]),
                        "|",
                        ("name", "=", state_name),
                        ("code", "=", state_name),
                    ],
                    limit=1,
                )
                if s_ids:
                    vals["state_id"] = s_ids[0]
                else:
                    logger.warning(
                        f"Estado '{state_name}' no encontrado para país '{country_code}'"
                    )
        else:
            logger.warning(f"País '{country_code}' no encontrado.")

    model_exec(models, db, uid, password, "res.company", "write", ids, vals)
    logger.info(f"Compañía actualizada: {vals['name']}")


def ensure_language(models, db, uid, password, lang_code: str):
    logger.info(f"Verificando idioma: {lang_code}")
    # Activa idioma si no está activo
    # 1) buscar en res.lang incluyendo inactivos
    ids = model_exec(
        models,
        db,
        uid,
        password,
        "res.lang",
        "search",
        [("code", "=", lang_code)],
        limit=1,
        context={"active_test": False},
    )
    if ids:
        # aseguramos active = True
        model_exec(
            models, db, uid, password, "res.lang", "write", ids, {"active": True}
        )
        logger.info(f"Idioma {lang_code} activado.")
        return

    logger.warning(
        f"Idioma {lang_code} no encontrado en res.lang. No se puede activar."
    )


def ensure_ir_config(models, db, uid, password, key: str, value: str):
    logger.info(f"Configurando parámetro {key} = {value}")
    ids = model_exec(
        models,
        db,
        uid,
        password,
        "ir.config_parameter",
        "search",
        [("key", "=", key)],
        limit=1,
    )
    if ids:
        model_exec(
            models,
            db,
            uid,
            password,
            "ir.config_parameter",
            "write",
            ids,
            {"value": value},
        )
    else:
        model_exec(
            models,
            db,
            uid,
            password,
            "ir.config_parameter",
            "create",
            [{"key": key, "value": value}],
        )


def ensure_default_lang(models, db, uid, password, lang_code: str):
    logger.info(f"Configurando idioma por defecto para nuevos registros: {lang_code}")
    # En Odoo, el idioma por defecto se suele manejar por el valor por defecto del campo 'lang' en 'res.partner'.
    # Buscamos si ya existe un valor por defecto para 'res.partner.lang'.
    ids = model_exec(
        models,
        db,
        uid,
        password,
        "ir.default",
        "search",
        [("field_id.model", "=", "res.partner"), ("field_id.name", "=", "lang")],
        limit=1,
    )

    # Necesitamos el ID del campo 'lang' de 'res.partner'
    field_ids = model_exec(
        models,
        db,
        uid,
        password,
        "ir.model.fields",
        "search",
        [("model", "=", "res.partner"), ("name", "=", "lang")],
        limit=1,
    )

    if not field_ids:
        logger.warning("No se encontró el campo 'lang' en 'res.partner'.")
        return

    vals = {
        "field_id": field_ids[0],
        "json_value": f'"{lang_code}"',
    }

    if ids:
        model_exec(models, db, uid, password, "ir.default", "write", ids, vals)
    else:
        model_exec(models, db, uid, password, "ir.default", "create", [vals])
    logger.info(f"Idioma por defecto '{lang_code}' aplicado a res.partner.")


def ensure_outgoing_mail_server(models, db, uid, password, smtp: Dict[str, Any]):
    logger.info(f"Configurando SMTP: {smtp.get('name')}")
    # Buscar por nombre
    name = smtp["name"]
    ids = model_exec(
        models,
        db,
        uid,
        password,
        "ir.mail_server",
        "search",
        [("name", "=", name)],
        limit=1,
    )
    vals = {
        "name": name,
        "smtp_host": smtp["smtp_host"],
        "smtp_port": int(smtp["smtp_port"]),
        "smtp_encryption": smtp.get("smtp_encryption", "starttls"),
        "smtp_user": smtp.get("smtp_user") or False,
        "smtp_pass": smtp.get("smtp_password") or False,
        "from_filter": smtp.get("from_filter") or False,
        "sequence": int(smtp.get("sequence", 10)),
        "active": True,
    }
    if ids:
        model_exec(models, db, uid, password, "ir.mail_server", "write", ids, vals)
        return ids[0]
    return model_exec(models, db, uid, password, "ir.mail_server", "create", [vals])


def ensure_incoming_mail_server(models, db, uid, password, imap: Dict[str, Any]):
    logger.info(f"Configurando IMAP/POP: {imap.get('name')}")
    name = imap["name"]
    ids = model_exec(
        models,
        db,
        uid,
        password,
        "fetchmail.server",
        "search",
        [("name", "=", name)],
        limit=1,
    )
    vals = {
        "name": name,
        "server_type": imap.get("server_type", "imap"),
        "server": imap["server_host"],
        "port": int(imap["server_port"]),
        "is_ssl": imap.get("is_ssl", True),
        "user": imap.get("user"),
        "password": imap.get("password"),
        "active": True,
    }
    if ids:
        model_exec(models, db, uid, password, "fetchmail.server", "write", ids, vals)
        return ids[0]
    return model_exec(models, db, uid, password, "fetchmail.server", "create", [vals])


def install_modules(models, db, uid, password, module_names: List[str]):
    # Instala módulos declarados (idempotente)
    logger.info(f"Verificando instalación de módulos: {module_names}")

    # Buscar módulos por name
    mods = model_exec(
        models,
        db,
        uid,
        password,
        "ir.module.module",
        "search_read",
        [("name", "in", module_names)],
        fields=["name", "state"],
    )

    found_names = {m["name"] for m in mods}
    missing = [m for m in module_names if m not in found_names]
    if missing:
        die(f"Módulos no encontrados en ir.module.module: {missing}")

    to_install_ids = []
    to_install_names = []

    for m in mods:
        if m["state"] not in ("installed", "to upgrade"):
            # Si está 'uninstalled' o 'uninstallable' (raro) lo marcamos
            to_install_ids.append(m["id"])
            to_install_names.append(m["name"])

    if not to_install_ids:
        logger.info("Todos los módulos ya están instalados.")
        return

    logger.info(f"Iniciando instalación de: {to_install_names}")

    # Instalar uno a uno para mejor feedback y evitar timeouts gigantes en lote
    for i, mod_name in enumerate(to_install_names):
        # Volvemos a buscar el ID por si acaso
        m_data = next((m for m in mods if m["name"] == mod_name), None)
        if not m_data:
            continue

        logger.info(f"Instalando [{i+1}/{len(to_install_names)}]: {mod_name}...")
        model_exec(
            models,
            db,
            uid,
            password,
            "ir.module.module",
            "button_immediate_install",
            [m_data["id"]],
        )
        logger.info(f"Módulo {mod_name} instalado (o acción desencadenada).")


def get_xml_id_res_id(models, db, uid, password, xml_id):
    if "." not in xml_id:
        return None
    module, name = xml_id.split(".", 1)
    # domain needs to be flat list of tuples
    domain = [("module", "=", module), ("name", "=", name)]
    ids = model_exec(
        models, db, uid, password, "ir.model.data", "search", domain, limit=1
    )
    if not ids:
        return None
    # read returns list of dicts
    data = model_exec(
        models, db, uid, password, "ir.model.data", "read", ids, ["res_id"]
    )
    if data and data[0].get("res_id"):
        return data[0]["res_id"]
    return None


def ensure_user(models, db, uid, password, user_data):
    login = user_data.get("login")
    if not login:
        return

    logger.info(f"Procesando usuario: {login}")

    # Check if user exists
    ids = model_exec(
        models,
        db,
        uid,
        password,
        "res.users",
        "search",
        [("login", "=", login)],
        limit=1,
    )

    # Defensive flatten if XMLRPC returns nested list
    if ids and isinstance(ids[0], list):
        ids = [i for sub in ids for i in sub]

    vals = {
        "name": user_data.get("name"),
        "login": login,
        "email": user_data.get("email"),
        "active": True,
        "lang": user_data.get("lang", "es_ES"),  # Default to es_ES as per user request
    }

    # Resolve groups
    group_ids = []
    for xml_id in user_data.get("groups", []):
        gid = get_xml_id_res_id(models, db, uid, password, xml_id)
        if gid:
            group_ids.append(gid)
        else:
            logger.warning(f"  [WARN] XML ID no encontrado: {xml_id}")

    target_uid = None

    if ids:
        # Update
        if "password" in user_data:
            vals["password"] = user_data["password"]

        model_exec(models, db, uid, password, "res.users", "write", ids, vals)
        logger.info(f"  Usuario {login} actualizado.")
        target_uid = ids[0]
    else:
        # Create
        if "password" in user_data:
            vals["password"] = user_data["password"]
        else:
            vals["password"] = login

        new_id = model_exec(models, db, uid, password, "res.users", "create", [vals])

        # Defensive check for create return
        if isinstance(new_id, list):
            new_id = new_id[0]

        logger.info(
            f"  Usuario {login} creado con password='{vals['password']}' (id={new_id})"
        )
        target_uid = new_id

    # Assign groups via Server Action to bypass XMLRPC field visibility issues
    group_xml_ids = user_data.get("groups", [])
    if group_xml_ids:
        # DEBUG: Dump available fields related to groups
        try:
            u_fields = model_exec(
                models,
                db,
                uid,
                password,
                "res.users",
                "fields_get",
                [],
                {"attributes": ["string", "type"]},
            )
            keys = sorted(u_fields.keys())
            group_keys = [k for k in keys if "group" in k or "user" in k]
            logger.info(f"DEBUG: res.users fields (partial): {group_keys}")
        except Exception as e:
            logger.error(f"DEBUG Error: {e}")

        # Find model_id for res.users
        res_users_model = model_exec(
            models,
            db,
            uid,
            password,
            "ir.model",
            "search",
            [("model", "=", "res.users")],
            limit=1,
        )

        if res_users_model:
            model_id = res_users_model[0]
            if isinstance(model_id, list):
                model_id = model_id[0]

            # Python code to run on server (using sudo to ensure rights)
            # Try to use the 'groups_id' field which standard in Odoo.
            # If that fails, we might need to inspect what fields are actually available.
            code = f"""
user = env['res.users'].search([('login', '=', '{login}')], limit=1)
xml_ids = {group_xml_ids}
for xml_id in xml_ids:
    group = env.ref(xml_id, False)
    if group and user:
        # Use direct SQL to bypass any ORM field visibility/validity issues
        # The relation table between res.groups and res.users is standard 'res_groups_users_rel'.
        env.cr.execute("INSERT INTO res_groups_users_rel (gid, uid) VALUES (%s, %s) ON CONFLICT DO NOTHING", (group.id, user.id))
        # Invalidate cache to ensure changes are seen
        user.invalidate_model() # Invalidate everything for safey
        group.invalidate_model()
            """

            action_vals = {
                "name": f"Provision User {login} Groups",
                "model_id": model_id,
                "state": "code",
                "code": code,
            }

            action_id = model_exec(
                models, db, uid, password, "ir.actions.server", "create", [action_vals]
            )

            if isinstance(action_id, list):
                action_id = action_id[0]

            model_exec(
                models, db, uid, password, "ir.actions.server", "run", [action_id]
            )
            logger.info(f"  Grupos asignados a {login} (Server Action).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument(
        "--only",
        choices=["mail", "modules", "langs", "params", "company", "users", "all"],
        default="all",
    )
    args = ap.parse_args()

    cfg = deep_env_expand(load_config(args.config))

    odoo = cfg.get("odoo", {})
    base_url = odoo.get("base_url")
    db = odoo.get("db")
    login = odoo.get("admin_login", "admin")
    password = odoo.get("admin_password")

    if not base_url or not db or not password:
        die(
            "Config incompleta: odoo.base_url, odoo.db y odoo.admin_password son obligatorios."
        )

    uid, models = xmlrpc_connect(base_url, db, login, password)
    logger.info(f"Conexión establecida. uid={uid} db={db}")

    # Ejecución secuencial según lógica

    # 1. Idiomas (lo primero, para que afecte a traducciones si se necesitan)
    if args.only in ("all", "langs"):
        inst = cfg.get("instance", {})
        langs = [inst.get("main_lang")] + (inst.get("extra_langs") or [])
        langs = [l for l in langs if l]
        for lang in langs:
            ensure_language(models, db, uid, password, lang)

        main_lang = inst.get("main_lang")
        if main_lang:
            ensure_default_lang(models, db, uid, password, main_lang)

        logger.info("Idiomas verificados.")

    # 2. Config de Parámetros (puede afectar URLs y comportamiento)
    if args.only in ("all", "params"):
        params = (cfg.get("settings", {}) or {}).get("ir_config_parameter", []) or []
        for p in params:
            ensure_ir_config(models, db, uid, password, p["key"], str(p["value"]))
        logger.info("Parámetros del sistema aplicados.")

    # 3. Compañía (metadata importante para informes/web)
    if args.only in ("all", "company"):
        comp = cfg.get("company", {})
        if comp:
            ensure_company(models, db, uid, password, comp)
        else:
            logger.info("No hay configuración de company en el YAML.")

    # 4. Módulos (lo más pesado al final)
    if args.only in ("all", "modules"):
        module_names = (cfg.get("modules", {}) or {}).get("install", []) or []
        if module_names:
            install_modules(models, db, uid, password, module_names)
            logger.info("Proceso de módulos finalizado.")
        else:
            logger.info("No hay lista de módulos a instalar.")

    # 5. Usuarios (dependen de grupos definidos por módulos)
    if args.only in ("all", "users"):
        users_list = cfg.get("users", []) or []
        for u in users_list:
            ensure_user(models, db, uid, password, u)
        if users_list:
            logger.info("Usuarios procesados.")
        else:
            logger.info("No hay usuarios definidos.")

    # 6. Mail
    if args.only in ("all", "mail"):
        mail = cfg.get("mail", {}) or {}
        smtp = mail.get("outgoing_smtp") or None
        if smtp:
            server_id = ensure_outgoing_mail_server(models, db, uid, password, smtp)
            logger.info(f"SMTP configurado correctamente (id={server_id}).")
        else:
            logger.info("No hay configuración SMTP pendiente.")

        imap = mail.get("incoming_imap") or None
        if imap:
            server_id = ensure_incoming_mail_server(models, db, uid, password, imap)
            logger.info(f"IMAP/POP configurado correctamente (id={server_id}).")
        else:
            logger.info("No hay configuración IMAP/POP pendiente.")

    logger.info("Provisioning completado con éxito.")


if __name__ == "__main__":
    main()
