import xmlrpc.client
import ssl

url = "https://aulavie.xtd.es/"
db = "aulavie"
username = "admin"
password = "xtendoo"  # The current admin password


def connect():
    ctx = ssl._create_unverified_context()
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", context=ctx)
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", context=ctx)
    uid = common.authenticate(db, username, password, {})
    return models, uid


def replace_admin():
    try:
        models, uid = connect()
        if not uid:
            # Maybe admin password already changed? Try 'xtendoo' if this is a re-run
            global password
            password = "xtendoo"
            models, uid = connect()
            if not uid:
                print("Auth failed with both 'admin' and 'xtendoo'")
                return

        print(f"Connected with UID: {uid}")

        # 1. Archive existing 'xtendoo' user (if it's not ID 2)
        xtendoo_ids = models.execute_kw(
            db, uid, password, "res.users", "search", [[("login", "=", "xtendoo")]]
        )
        for xid in xtendoo_ids:
            if xid != 2:
                print(f"Archiving existing 'xtendoo' user (ID {xid})...")
                models.execute_kw(
                    db,
                    uid,
                    password,
                    "res.users",
                    "write",
                    [[xid], {"login": f"xtendoo_archived_{xid}", "active": False}],
                )

        # 2. Update Admin (ID 2) to be Xtendoo
        print("Updating Admin (ID 2) to 'Xtendoo'...")
        models.execute_kw(
            db,
            uid,
            password,
            "res.users",
            "write",
            [
                [2],
                {
                    "name": "Xtendoo",
                    "login": "xtendoo",
                    "email": "manuelcalero@xtendoo.es",
                    "password": "xtendoo",
                    "lang": "es_ES",
                    # Ensure it has the correct image/preferences if needed, but this is enough strictly permissions-wise
                },
            ],
        )
        print("Admin user successfully replaced by Xtendoo.")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    replace_admin()
