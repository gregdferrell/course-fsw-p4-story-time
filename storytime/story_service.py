from sqlalchemy.orm.exc import NoResultFound

from storytime.storytime_db_init import Category, Story, User, db_session


# User functions
def create_user(user: User):
    db_session.add(user)
    db_session.commit()
    return user.id


def get_user_info(user_id: int):
    try:
        return db_session.query(User).filter_by(id=user_id).one()
    except NoResultFound:
        return None


def get_user_id_by_email(email: str):
    try:
        user = db_session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


def get_user_by_email(email: str):
    try:
        return db_session.query(User).filter_by(email=email).one()
    except NoResultFound:
        return None


# Story functions
def create_story(story: Story):
    db_session.add(story)
    db_session.commit()
    return story.id


def update_story(story: Story):
    db_session.add(story)
    db_session.commit()
    return


def deactivate_story(story_id: int):
    story = db_session.query(Story).filter_by(id=story_id).one()
    story.active = False
    db_session.add(story)
    db_session.commit()
    return


def get_stories():
    return db_session.query(Story).filter_by(active=True)


def get_stories_by_category_id(category_id: int):
    return db_session.query(Story).filter(Story.categories.any(Category.id == category_id))


def get_stories_by_user_id(user_id: int):
    return db_session.query(Story).filter_by(active=True, user_id=user_id)


def get_story_by_id(story_id: int):
    try:
        return db_session.query(Story).filter_by(id=story_id).one()
    except NoResultFound:
        return None


# Category functions
def create_category(category: Category):
    db_session.add(category)
    db_session.commit()
    return category.id


def get_category_by_id(category_id: int):
    try:
        return db_session.query(Category).filter_by(id=category_id).one()
    except NoResultFound:
        return None


def get_category_by_label(category_label: str):
    try:
        return db_session.query(Category).filter_by(label=category_label).one()
    except NoResultFound:
        return None
