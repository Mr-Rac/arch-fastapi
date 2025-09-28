from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies.auth import check_scopes
from app.api.dependencies.mysql import AuthMySQLDep
from app.api.dependencies.redis import AuthRedisDep
from app.domains.auth.schema import *
from app.domains.auth.service import AuthService
from app.domains.base_schema import BaseResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=BaseResponse, description="login")
async def login(
        form: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: AuthMySQLDep,
        redis: AuthRedisDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.login, form, session, redis)


@router.post("/refresh-token", response_model=BaseResponse, description="refresh token")
async def refresh_token(
        body: RefreshRequestBody,
        redis: AuthRedisDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.refresh_token, body, redis)


@router.post("/logout", response_model=BaseResponse, description="logout")
async def logout(
        body: LogoutRequestBody,
        session: AuthMySQLDep,
        redis: AuthRedisDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.logout, body, session, redis)


@router.post("/user/select", dependencies=[Depends(check_scopes("user:select"))])
async def select_user(
        body: UserSelect,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.select_user, session, body)


@router.post("/user/create", dependencies=[Depends(check_scopes("user:create"))])
async def create_user(
        body: UserCreate,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.create_user, session, body)


@router.post("/user/update", dependencies=[Depends(check_scopes("user:update"))])
async def update_user(
        body: UserUpdate,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.update_user, session, body)


@router.post("/user/delete", dependencies=[Depends(check_scopes("user:delete"))])
async def delete_user(
        body: UserDelete,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.delete_user, session, body)


@router.post("/role/select", dependencies=[Depends(check_scopes("role:select"))])
async def select_role(
        body: RoleSelect,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.select_role, session, body)


@router.post("/role/create", dependencies=[Depends(check_scopes("role:create"))])
async def create_role(
        body: RoleCreate,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.create_role, session, body)


@router.post("/role/update", dependencies=[Depends(check_scopes("role:update"))])
async def update_role(
        body: RoleUpdate,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.update_role, session, body)


@router.post("/role/delete", dependencies=[Depends(check_scopes("role:delete"))])
async def delete_role(
        body: RoleDelete,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.delete_role, session, body)


@router.post("/permission/select", dependencies=[Depends(check_scopes("permission:select"))])
async def select_permission(
        body: PermissionSelect,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.select_permission, session, body)


@router.post("/permission/create", dependencies=[Depends(check_scopes("permission:create"))])
async def create_permission(
        body: PermissionCreate,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.create_permission, session, body)


@router.post("/permission/update", dependencies=[Depends(check_scopes("permission:update"))])
async def update_permission(
        body: PermissionUpdate,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.update_permission, session, body)


@router.post("/permission/delete", dependencies=[Depends(check_scopes("permission:delete"))])
async def delete_permission(
        body: PermissionDelete,
        session: AuthMySQLDep,
        service: AuthService = Depends(AuthService.instance)
) -> BaseResponse:
    return await service.safe_execute(service.delete_permission, session, body)
