from coverage.files import os
from sqlalchemy import Column, Integer, String, Table, MetaData, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from bookbot import config_holder


engine = create_engine(config_holder.config["DB_PATH"], echo=True)

Base = declarative_base()


class BookedRange(Base):
    __tablename__ = 'booked_range'
    id = Column(Integer, primary_key=True)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    username = Column(Integer)

    def __repr__(self):
        return str(f"{type(self)}:{self.__dict__}")


class UserInfo(Base):
    __tablename__ = 'user_info'
    id = Column(Integer, primary_key=True)
    phone = Column(String)
    name = Column(String)
    username = Column(Integer, unique=True)
    userlink = Column(String)

    def __repr__(self):
        return str(f"{type(self)}:{self.__dict__}")


Table('booked_range', MetaData(bind=None),
            Column('id', Integer(), primary_key=True, nullable=False),
            Column('start_date', DateTime()),
            Column('end_date', DateTime()),
            Column('username', Integer()))

Table('user_info', MetaData(bind=None),
            Column('id', Integer(), primary_key=True, nullable=False),
            Column('phone', String()),
            Column('name', String()),
            Column('userlink', String()),
            Column('username', Integer(), unique=True))

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()
