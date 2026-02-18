import xmlrpc.client, ssl, json

url = "https://aulavie.xtd.es/"
db = "aulavie"
u = "admin"
p = "admin"
try:
    ctx = ssl._create_unverified_context()
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", context=ctx)
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", context=ctx)
    uid = common.authenticate(db, u, p, {})
    if uid:
        fields = models.execute_kw(
            db, uid, p, "res.users", "fields_get", [], {"attributes": ["type"]}
        )
        with open("res_users_fields.json", "w") as f:
            json.dump(list(fields.keys()), f)
        print("Done")
    else:
        print("Auth failed")
except Exception as e:
    print(f"Error: {e}")
