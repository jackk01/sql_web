from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from io import BytesIO
from urllib.parse import quote

from app.api.dependencies import get_auth_service, get_current_user, get_query_service
from app.models.schemas import (
    AuthResponse,
    ConnectionPayload,
    ConnectionProfile,
    DatabasesResponse,
    LoginRequest,
    QueryRequest,
    QueryResponse,
    RegisterRequest,
    TablesResponse,
    UserPublic,
)
from app.services.auth_service import AuthService
from app.services.query_service import QueryService


router = APIRouter()


@router.get("/health")
def healthcheck():
    return {"status": "ok"}


@router.post("/auth/register", response_model=AuthResponse)
def register(
    payload: RegisterRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    session = service.register(payload)
    _write_session_cookie(response, session.session_token, service)
    return AuthResponse(user=session.user)


@router.post("/auth/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    session = service.login(payload)
    _write_session_cookie(response, session.session_token, service)
    return AuthResponse(user=session.user)


@router.post("/auth/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    session_token = request.cookies.get(service.settings.session_cookie_name)
    service.logout(session_token)
    response.delete_cookie(service.settings.session_cookie_name, httponly=True, samesite="lax")


@router.get("/auth/me", response_model=AuthResponse)
def me(current_user: UserPublic = Depends(get_current_user)):
    return AuthResponse(user=current_user)


@router.get("/db-types")
def list_db_types(
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    return service.list_database_types()


@router.get("/connections")
def list_connections(
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    return service.list_connections(current_user.id)


@router.get("/connections/{connection_id}", response_model=ConnectionProfile)
def get_connection(
    connection_id: str,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    return service.get_connection(connection_id, current_user.id)


@router.post("/connections")
def create_connection(
    payload: ConnectionPayload,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        return service.create_connection(payload, current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/connections/{connection_id}")
def update_connection(
    connection_id: str,
    payload: ConnectionPayload,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        return service.update_connection(connection_id, payload, current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/connections/{connection_id}", status_code=204)
def delete_connection(
    connection_id: str,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    service.delete_connection(connection_id, current_user.id)


@router.post("/connections/test")
def test_connection(
    payload: ConnectionPayload,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        return service.test_connection(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/connections/{connection_id}/databases", response_model=DatabasesResponse)
def list_databases(
    connection_id: str,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        return DatabasesResponse(items=service.list_databases(connection_id, current_user.id))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/connections/{connection_id}/tables", response_model=TablesResponse)
def list_tables(
    connection_id: str,
    database: str,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        return TablesResponse(items=service.list_tables(connection_id, database, current_user.id))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/query/execute", response_model=QueryResponse)
def execute_query(
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        return service.execute_query(payload, current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/query/export")
def export_query(
    payload: QueryRequest,
    service: QueryService = Depends(get_query_service),
    current_user: UserPublic = Depends(get_current_user),
):
    try:
        content, filename = service.export_query(payload, current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quoted_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{quoted_filename}",
    }
    return StreamingResponse(
        BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


def _write_session_cookie(response: Response, session_token: str, service: AuthService) -> None:
    response.set_cookie(
        key=service.settings.session_cookie_name,
        value=session_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=service.settings.session_ttl_hours * 3600,
    )
