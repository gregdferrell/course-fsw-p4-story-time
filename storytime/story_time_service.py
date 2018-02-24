#
# Story Time App
# Exposes functions that connect to and query the storytime DB
#

from typing import List

from sqlalchemy.orm.exc import NoResultFound
from werkzeug.datastructures import FileStorage

from storytime import file_storage_service
from storytime.app import upload_set_photos
from storytime.story_time_db_init import Category, Story, UploadFile, User, db_engine, db_session

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
def create_story(story: Story, image_file: FileStorage = None):
    """
    Creates the given story in the DB.
    :param story: the story to create
    :param image_file: the image file to save (or None)
    :return: an integer representing the primary key of the object created
    """
    try:
        if image_file:
            upload_file = file_storage_service.save_file(file=image_file, upload_set=upload_set_photos)
            create_upload_file(upload_file)
            story.upload_file_id = upload_file.id
        db_session.add(story)
        db_session.commit()
        return story.id
    except Exception as exc:
        db_session.rollback()
        raise exc


def update_story(story: Story, remove_existing_image: bool, new_image_file):
    """

    :param story: the story to update
    :param remove_existing_image: a flag indicating whether or not to remove the existing image from the story
    :param new_image_file: a new image file to associate with the story
    """
    # Save the old upload file for deletion later (if instructed to remove it)
    old_upload_file_to_delete = story.upload_file if remove_existing_image and story.upload_file else None

    try:
        # Removing existing image from story
        if remove_existing_image:
            story.upload_file = None

        # Save new file and add new image to story
        if new_image_file:
            story.upload_file = file_storage_service.save_file(file=new_image_file, upload_set=upload_set_photos)

        # Save story to DB
        db_session.add(story)
        db_session.execute("UPDATE story SET date_last_modified = TIMEZONE('utc', CURRENT_TIMESTAMP) WHERE id = :id",
                           {'id': story.id})

        # Remove old file from DB
        if old_upload_file_to_delete:
            db_session.delete(old_upload_file_to_delete)

        db_session.commit()
    except Exception as exc:
        db_session.rollback()
        raise exc

    # Finally, delete the old image from the file system (do this last so we only delete when we know everything
    # else has succeeded)
    if old_upload_file_to_delete:
        file_storage_service.delete_file(file=old_upload_file_to_delete, upload_set=upload_set_photos)


def delete_story(story_id: int):
    """
    Permanently deletes the story for the given story_id
    :param story_id: the primary key of the story to delete
    """
    try:
        story = db_session.query(Story).filter_by(id=story_id).one()
        upload_file = story.upload_file
        story.categories = []
        db_session.delete(story)
        if upload_file:
            file_storage_service.delete_file(file=upload_file, upload_set=upload_set_photos)
            db_session.delete(upload_file)
        db_session.commit()
    except Exception as exc:
        db_session.rollback()
        raise exc


def get_published_stories_count():
    """
    Gets the count of all published stories.
    :return: the number of published stories
    """
    return db_session.query(Story).filter_by(published=True).count()


def get_published_stories(count: int = None):
    """
    Gets all published stories.
    :param count: the number of stories to retrieve
    :return: a list of stories
    """
    query = db_session.query(Story).filter_by(published=True).order_by(Story.date_created.desc())
    if count:
        query = query.limit(count)
    return query.all()


def get_published_stories_by_category_id(category_id: int):
    """
    Gets all published stories for the given category_id.
    :param category_id: the primary key for the category to search on
    :return: a list of stories
    """
    return db_session.query(Story).filter_by(published=True).filter(
        Story.categories.any(Category.id == category_id)).all()


def get_stories_by_user_id(user_id: int):
    """
    Gets all stories for the given user id.
    :param user_id: the primary key for the user to search on
    :return: a list of stories ordered by date last modified descending
    """
    return db_session.query(Story).filter_by(user_id=user_id).order_by(Story.date_last_modified.desc()).all()


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
    :return: the story or None if none exist
    """
    with db_engine.connect() as con:
        rs = con.execute(SQL_GET_STORY_RANDOM)
        row = rs.fetchone()
        return get_story_by_id(story_id=row[0]) if row else None


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


# Upload File functions
def create_upload_file(file: UploadFile):
    """
    Creates the given upload file in the DB.
    :param file: the upload file
    :return: an integer representing the primary key of the object created
    """
    db_session.add(file)
    db_session.commit()
    return file.id


def get_upload_file_by_id(upload_file_id: int):
    """
    Gets an upload file by id
    :param upload_file_id: the primary key for the upload file to search for
    :return: the upload file or None
    """
    try:
        return db_session.query(UploadFile).filter_by(id=upload_file_id).one()
    except NoResultFound:
        return None
