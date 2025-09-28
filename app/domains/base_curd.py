from typing import TypeVar, Type, Generic, Sequence

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

from app.domains.base_exception import Error
from app.domains.base_schema import BaseSelect

M = TypeVar("M")


class Curd(Generic[M]):
    model: Type[M]

    @classmethod
    async def select(cls, session: AsyncSession, model_in: "SQLModel", one: bool = True) -> M | Sequence[M]:
        model_in = model_in.model_dump(exclude_unset=True, exclude_defaults=True)
        if not model_in:
            raise Exception(Error.INVALID_ARGS)
        conditions = [getattr(cls.model, field) == value for field, value in model_in.items()]
        stmt = select(cls.model).where(*conditions)
        result = await session.execute(stmt)
        result = result.scalars()
        return result.one_or_none() if one else result.all()

    @classmethod
    async def create(cls, session: AsyncSession, model_in: "SQLModel", update: dict | None = None) -> M:
        try:
            model = cls.model.model_validate(model_in, update=update)
            session.add(model)
        except IntegrityError as exc:
            await session.rollback()
            raise Exception(exc.args[0])
        except:
            await session.rollback()
            raise
        await session.commit()
        await session.refresh(model)
        return model

    @classmethod
    async def update(cls, session: AsyncSession, model_in: "SQLModel", update: dict | None = None) -> M:
        try:
            model = await cls.select(session, BaseSelect(id=model_in.id))
            model.sqlmodel_update(model_in.model_dump(exclude_unset=True, exclude_defaults=True), update=update)
        except IntegrityError as exc:
            await session.rollback()
            raise Exception(exc.args[0])
        except:
            await session.rollback()
            raise
        await session.commit()
        await session.refresh(model)
        return model

    @classmethod
    async def delete(cls, session: AsyncSession, model_in: "SQLModel") -> None:
        try:
            model = await cls.select(session, BaseSelect(id=model_in.id))
            await session.delete(model)
        except IntegrityError as exc:
            await session.rollback()
            raise Exception(exc.args[0])
        except:
            await session.rollback()
            raise
        await session.commit()
