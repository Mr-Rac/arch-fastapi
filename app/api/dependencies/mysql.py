from typing import AsyncGenerator, Annotated

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.base_exception import Error


async def get_auth_mysql(request: Request) -> AsyncGenerator[AsyncSession, None]:
    if session_maker := getattr(request.state, "auth_mysql_session_maker", None):
        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=Error.INVALID_MYSQL,
        )


AuthMySQLDep = Annotated[AsyncSession, Depends(get_auth_mysql)]
