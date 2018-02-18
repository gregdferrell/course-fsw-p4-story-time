#
# Story Time App
# Exposes core SQL Alchemy & DB objects to the rest of the app
#

import configparser
import os
from typing import List

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Table, Text, create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.types import DateTime

Base = declarative_base()


class User(Base):
    """
    User is a Python SQL Alchemy representation of the sec_user DB table.
    """
    __tablename__ = 'sec_user'
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=False, unique=True)
    active = Column(Boolean, nullable=False)


class Story(Base):
    """
    Story is a Python SQL Alchemy representation of the story DB table.
    """
    __tablename__ = 'story'
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    story_text = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False)
    # TODO: Not sure why the server_default is needed to make the DEFAULT at the column definition level work
    date_created = Column(DateTime(timezone=False), server_default=text("NOW() AT TIME ZONE 'utc'"))
    date_last_modified = Column(DateTime(timezone=False), server_default=text("NOW() AT TIME ZONE 'utc'"))
    categories = relationship("Category", secondary=lambda: story_category_join_table, cascade='all')
    user_id = Column(Integer, ForeignKey('sec_user.id'))
    user = relationship("User")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'story_text': self.story_text,
            'user_id': self.user_id,
            'date_created': self.date_created,
            'date_last_modified': self.date_last_modified,
            'categories': [category.serialize for category in self.categories]
        }


class Category(Base):
    """
    Category is a Python SQL Alchemy representation of the category DB table.
    """
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    label = Column(Text, nullable=False)
    description = Column(Text)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'label': self.label,
            'description': self.description
        }


# Represents join table story_category
story_category_join_table = Table('story_category', Base.metadata,
                                  Column('story_id', Integer, ForeignKey('story.id')),
                                  Column('category_id', Integer, ForeignKey('category.id'))
                                  )

# Get DB config from external config
db_config = configparser.ConfigParser()
db_config.read(os.path.join(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config/story_time.ini')))
db_server = db_config['DEFAULT']['db.server']
db_port = db_config['DEFAULT']['db.port']
db_name = db_config['DEFAULT']['db.name']
db_user = db_config['DEFAULT']['db.user']
db_password = db_config['DEFAULT']['db.password']

# Create an Engine, which the session will use for connection resources
db_engine = create_engine('postgresql://{}:{}@{}:{}/{}'.format(db_user, db_password, db_server, db_port, db_name))

# Create a configured "Session" class
Session = sessionmaker(bind=db_engine)

# Create a session
db_session = Session()
