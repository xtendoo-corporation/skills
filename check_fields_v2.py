import xmlrpc.client
import ssl

url = "https://aulavie.xtd.es/"
db = "aulavie"
username = "admin"
password = "admin"

try:
    ctx = ssl._create_unverified_context()
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", context=ctx)
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", context=ctx)
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("Auth failed")
        exit(1)

    print(f"UID: {uid}")

    # Check fields of res.users filtering for 'group'
    fields = models.execute_kw(
        db, uid, password, "res.users", "fields_get", [], {"attributes": ["type"]}
    )
    keys = sorted(fields.keys())
    group_fields = [k for k in keys if "group" in k]
    print(f"Group related fields on res.users: {group_fields}")

    # Check if groups_id is in keys
    print(f"groups_id present: {'groups_id' in keys}")

except Exception as e:
    print(f"Error: {e}")
