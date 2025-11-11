# orders/authz.py
from django.conf import settings
from social_django.models import UserSocialAuth

def get_subject(request) -> str:
    user = request.user
    auth = user.social_auth.filter(provider="auth0").first()
    if not auth:
        return "anonymous"
    return auth.extra_data.get("id_token_payload", {}).get("sub") or auth.uid

def get_role(request) -> str|None:
    user = request.user
    auth = user.social_auth.filter(provider="auth0").first()
    if not auth:
        return None
    payload = auth.extra_data.get("id_token_payload", {})
    ns = settings.SOCIAL_AUTH_AUTH0_DOMAIN
    return payload.get(f"{ns}/role")
