from sqlalchemy.orm import as_declarative


@as_declarative()
class BaseModel:
    pass

