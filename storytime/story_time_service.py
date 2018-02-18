#
# Story Time App
# Exposes functions that connect to and query the storytime DB
#

from typing import List

from sqlalchemy.orm.exc import NoResultFound

from storytime.story_time_db_init import Category, Story, User, db_engine, db_session

SQL_GET_STORY_RANDOM = 'SELECT id FROM story ORDER BY random() LIMIT 1'


# User functions
def create_user(user: User):
    """
    Creates the given user in the DB.
    :param user: the user to create
    :return: an integer representing the primary key of the object created
    """
    db_session.add(user)
    db_session.commit()
    return user.id


def get_user_info(user_id: int):
    """
    Gets user info by user id.
    :param user_id: the primary key of the user
    :return: the user object
    """
    try:
        return db_session.query(User).filter_by(id=user_id).one()
    except NoResultFound:
        return None


def get_user_id_by_email(email: str):
    """
    Gets the user_id of the user for the given email address.
    :param email: the email address to use in the lookup
    :return: an integer representing the primary key of the user object retrieved
    """
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


def get_user_by_email(email: str):
    """
    Gets the User object for the given email address.
    :param email: the email address to use in the lookup
    :return: the user object
    """
    try:
        return db_session.query(User).filter_by(email=email).one()
    except NoResultFound:
        return None


# Story functions
def create_story(story: Story):
    """
    Creates the given story in the DB.
    :param story: the story to create
    :return: an integer representing the primary key of the object created
    """
    db_session.add(story)
    db_session.commit()
    return story.id


def update_story(story: Story):
    """
    Update the given story in the DB.
    :param story: the story to update
    """
    db_session.add(story)
    db_session.commit()
    return


def unpublish_story(story_id: int):
    """
    Unpublishes the story for the given story_id
    :param story_id: the primary key of the story to deactivate
    """
    story = db_session.query(Story).filter_by(id=story_id).one()
    story.published = False
    db_session.add(story)
    db_session.commit()
    return


def get_stories():
    """
    Gets all published stories.
    :return: a list of stories
    """
    return db_session.query(Story).filter_by(published=True).all()


def get_stories_by_category_id(category_id: int):
    """
    Gets all published stories for the given category_id.
    :param category_id: the primary key for the category to search on
    :return: a list of stories
    """
    return db_session.query(Story).filter_by(published=True).filter(Story.categories.any(Category.id == category_id)).all()


def get_stories_by_user_id(user_id: int):
    """
    Gets all stories for the given user id.
    :param user_id: the primary key for the user to search on
    :return: a list of stories
    """
    return db_session.query(Story).filter_by(user_id=user_id).all()


def get_story_by_id(story_id: int):
    """
    Gets a story by id
    :param story_id: the primary key for the story to search for
    :return: the story or None
    """
    try:
        return db_session.query(Story).filter_by(id=story_id).one()
    except NoResultFound:
        return None


def get_story_random():
    """
    Gets a random story
    :return: the story or None
    """
    with db_engine.connect() as con:
        rs = con.execute(SQL_GET_STORY_RANDOM)
        row = rs.fetchone()
        story_id = row[0]

    if not story_id:
        raise Exception('Unexpected error occurred getting random story')

    return get_story_by_id(story_id=story_id)


# Category functions
def create_category(category: Category):
    """
    Creates the given category in the DB.
    :param category: the category to create
    :return: an integer representing the primary key of the object created
    """
    db_session.add(category)
    db_session.commit()
    return category.id


def get_categories():
    """
    Gets all active categories.
    :return: a list of categories
    """
    return db_session.query(Category).order_by(Category.label.asc()).all()


def get_category_by_id(category_id: int):
    """
    Gets a category by id
    :param category_id: the primary key for the category to search for
    :return: the category or None
    """
    try:
        return db_session.query(Category).filter_by(id=category_id).one()
    except NoResultFound:
        return None


def get_categories_by_ids(category_ids: List):
    """
    Gets a list of categories by their ids
    :param category_ids: the list of category ids
    :return: a list of categories
    """
    try:
        return db_session.query(Category).filter(Category.id.in_(category_ids)).all()
    except NoResultFound:
        return None


def get_category_by_label(category_label: str):
    """
    Gets a category by label
    :param category_id: the unique label for the category to search for
    :return: the category or None
    """
    try:
        return db_session.query(Category).filter_by(label=category_label).one()
    except NoResultFound:
        return None
