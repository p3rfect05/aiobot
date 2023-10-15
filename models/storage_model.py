import datetime

from sqlalchemy import ForeignKey, DATETIME, Date, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import BaseModel

class StorageModel(BaseModel):
    __tablename__ = 'file_storage'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    file_id: Mapped[str] = mapped_column(primary_key=True)
    file_type: Mapped[str] = mapped_column()
    file_name: Mapped[str] = mapped_column()

    user: Mapped["UserModel"] = relationship(back_populates='files', uselist=False)
    user_fk: Mapped[int] = mapped_column(ForeignKey('users.user_id'))

    time_create = Column(DateTime, default=datetime.datetime.now)
