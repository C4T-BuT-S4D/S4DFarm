import copy
import requests
import jwt

API_PREFIX = 'api/capsule/v1'
PUBLIC_KEY_ENDPOINT = 'public_key'

def get_public_key(host):
    r = requests.get("%s/%s/%s" % (host, API_PREFIX, PUBLIC_KEY_ENDPOINT))

    if r is not None and r.status_code == requests.codes.ok:
        return r.text

    raise ConnectionError("Could not get public key to check flags from %s." % host)

def decode(key, capsule):
    payload = jwt.decode(
        capsule,
        algorithms=['ES256', 'RS256'],
        key=key
        )
    return payload

def validate_flags(flags, config):
    key = config.get('SYSTEM_SERVER_KEY')
    if not key:
        key = get_public_key(config['SYSTEM_HOST'])

    for item in flags:
        item = copy.deepcopy(item)
        flag = item['flag']
        if flag.startswith('VolgaCTF{'):
            flag = flag[len('VolgaCTF{') : -len('}')]

        try:
            item['flag'] = decode(key, flag)
            yield item
        except Exception:
            continue
