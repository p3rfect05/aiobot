import datetime

from sqlalchemy import DateTime, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel


class ReminderModel(BaseModel):
    __tablename__ = "reminders"
    reminder_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    reminder_type: Mapped[str]
    reminder_desc: Mapped[str]
    user: Mapped["UserModel"] = relationship(back_populates="reminders", uselist=False)
    user_fk: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    time_create = Column(DateTime, default=datetime.datetime.now)
    time_triggers = Column(DateTime)
