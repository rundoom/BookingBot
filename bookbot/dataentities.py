from coverage.files import os
from sqlalchemy import Column, Integer, String, Table, MetaData, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

resource_dir = os.path.join(os.path.dirname(__file__), "resource")
if not os.path.exists(resource_dir):
    os.makedirs(resource_dir)

engine = create_engine('sqlite:///resource/bot_data.db', echo=True)

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
            Column('username', Integer(), unique=True))

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()
