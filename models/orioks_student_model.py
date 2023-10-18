import datetime

from sqlalchemy import ForeignKey, DateTime, Column
from sqlalchemy.orm import Mapped, relationship, mapped_column

from .base_model import BaseModel


class OrioksGroupsModel(BaseModel):
    __tablename__ = 'orioks_groups'
    group_id: Mapped[str] = mapped_column(primary_key=True)
    students: Mapped[list["OrioksStudentsModel"]] = relationship(back_populates='group', lazy='selectin',
                                                                 uselist=True)

class OrioksStudentsModel(BaseModel):
    __tablename__ = 'orioks_students'
    student_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group: Mapped["OrioksGroupsModel"] = relationship(back_populates='students', lazy='selectin',
                                                      uselist=False)
    group_fk = mapped_column(ForeignKey('orioks_groups.group_id'))
    user: Mapped["UserModel"] = relationship(back_populates='orioks_student', uselist=False, lazy='selectin')
    user_fk: Mapped[int] = mapped_column(ForeignKey('users.user_id'))
    access_token: Mapped[str] = mapped_column(default=None)
    full_name: Mapped[str]
    time_create = Column(DateTime, default=datetime.datetime.now)
