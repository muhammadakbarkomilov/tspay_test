from rest_framework.throttling import SimpleRateThrottle

class ShopAccessTokenThrottle(SimpleRateThrottle):
    scope = 'shop'

    def get_cache_key(self, request, view):
        token = request.data.get('access_token')
        if not token:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': token}