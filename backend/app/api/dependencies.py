from fastapi import Depends, Request

from app.services.auth_service import AuthService
from app.services.query_service import QueryService
from app.storage.auth_store import AuthStore
from app.storage.profile_store import ProfileStore


def get_auth_store() -> AuthStore:
    return AuthStore()


def get_profile_store() -> ProfileStore:
    return ProfileStore()


def get_auth_service(store: AuthStore = Depends(get_auth_store)) -> AuthService:
    return AuthService(store)


def get_query_service(store: ProfileStore = Depends(get_profile_store)) -> QueryService:
    return QueryService(store)


def get_current_user(request: Request, service: AuthService = Depends(get_auth_service)):
    session_token = request.cookies.get(service.settings.session_cookie_name)
    return service.get_current_user(session_token)

