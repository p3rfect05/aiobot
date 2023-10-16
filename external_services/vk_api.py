import urllib.parse


auth_url = 'https://oauth.vk.com/authorize'


def get_vk_auth_link() -> str:
    redirect_uri = 'https://oauth.vk.com/blank.html'
    client_id = '51547487'
    display = 'popup'
    response_type = 'token'
    scope = 'offline'
    params={'redirect_uri' : redirect_uri, 'client_id' : client_id,
            'display' : display, 'response_type' : response_type,
            'scope' : scope}
    return f'{auth_url}?{urllib.parse.urlencode(params)}'


