import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from string import ascii_letters, digits
from random import sample


def random_key():
    return ''.join(sample(ascii_letters + digits, 30))

class ApiKey(SqlAlchemyBase):
    __tablename__ = 'api_keys'
    key = sqlalchemy.Column(sqlalchemy.String, default=random_key,
                            unique=True, primary_key=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    user = orm.relationship('User')
