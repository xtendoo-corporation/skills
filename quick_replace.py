import xmlrpc.client
import ssl

url = 'https://aulavie.xtd.es/'
db = 'aulavie'
username = 'admin'
password = 'admin'

ctx = ssl._create_unverified_context()
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=ctx)
try:
    uid = common.authenticate(db, username, password, {})
    if not uid:
        password = 'xtendoo'
        uid = common.authenticate(db, username, password, {})
    
    if uid:
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ctx)
        
        # 1. Archive other xtendoo users
        other_ids = models.execute_kw(db, uid, password, 'res.users', 'search', [[('login', '=', 'xtendoo'), ('id', '!=', 2)]])
        if other_ids:
            models.execute_kw(db, uid, password, 'res.users', 'write', [other_ids, {'active': False, 'login': 'xtendoo_archived'}])
            print('Archived existing xtendoo user')

        # 2. Update Admin (id 2)
        models.execute_kw(db, uid, password, 'res.users', 'write', [[2], {
            'name': 'Xtendoo',
            'login': 'xtendoo',
            'email': 'manuelcalero@xtendoo.es',
            'password': 'xtendoo'
        }])
        print('Updated Admin (ID 2) to Xtendoo')
    else:
        print('Auth failed')

except Exception as e:
    print(e)

