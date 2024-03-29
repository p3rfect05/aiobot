from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    files: Mapped[list["StorageModel"]] = relationship(
        back_populates="user", uselist=True, lazy="selectin"
    )
    reminders: Mapped[list["ReminderModel"]] = relationship(
        back_populates="user", uselist=True, lazy="selectin"
    )
    orioks_student: Mapped["OrioksStudentsModel"] = relationship(
        back_populates="user", uselist=False, lazy="selectin"
    )
