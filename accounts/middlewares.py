from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

class BlockedUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user = request.user
        if user.is_authenticated and hasattr(user, 'is_blocked') and user.is_blocked:
            if request.path.startswith('api/'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Sizning hisobingiz bloklangan. Iltimos, admin bilan bogʻlaning.',
                    'code': 'user_blocked'
                }, status=403)