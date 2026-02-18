import xmlrpc.client
import ssl

url = "https://aulavie.xtd.es/"
db = "aulavie"
username = "admin"
password = "admin"

try:
    context = ssl._create_unverified_context()
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", context=context)
    uid = common.authenticate(db, username, password, {})
    print(f"UID: {uid}")

    if uid:
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", context=context)
        # Check fields of res.users
        fields = models.execute_kw(
            db,
            uid,
            password,
            "res.users",
            "fields_get",
            [],
            {"attributes": ["string", "type"]},
        )
        print(f"res.users fields: {list(fields.keys())}")

except Exception as e:
    print(f"Error: {e}")
