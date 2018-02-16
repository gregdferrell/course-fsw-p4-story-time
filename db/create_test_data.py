#
# Story Time App
# Creates test data for the integration tests and development environment setup.
#

import json

import httplib2
import time

from storytime import story_time_service
from storytime.story_time_db_init import Category, Story, User, db_session


def delete_and_recreate_test_data():
    """
    Deletes and recreates Story Time test data.
    """
    try:
        # Delete all data
        for story in db_session.query(Story):
            story.categories = []
        num_rows_deleted = db_session.query(Story).delete()
        print('Deleted {} stories'.format(num_rows_deleted))
        num_rows_deleted = db_session.query(Category).delete()
        print('Deleted {} categories'.format(num_rows_deleted))
        num_rows_deleted = db_session.query(User).delete()
        print('Deleted {} users'.format(num_rows_deleted))
        db_session.commit()

        # Create test data
        # Users
        user_1 = story_time_service.create_user(
            User(name='gregdferrell', email='gferrell20@gmail.com', active=True))
        user_2 = story_time_service.create_user(
            User(name='Jane Doe', email='janedoe@email.com', active=True))
        user_3 = story_time_service.create_user(
            User(name='John Smith', email='jonsmith@email.com', active=True))
        num_rows_created = db_session.query(User).count()
        print('Created {} users'.format(num_rows_created))

        # Categories
        cat_scary_id = story_time_service.create_category(Category(label='Scary', description='Scary stories!'))
        cat_funny_id = story_time_service.create_category(Category(label='Funny', description='Funny stories!'))
        cat_animal_id = story_time_service.create_category(
            Category(label='Animals', description='Stories about animials!'))
        cat_musical_id = story_time_service.create_category(
            Category(label='Musical', description='Stories that can be sung to music!'))
        cat_history_id = story_time_service.create_category(
            Category(label='History', description='Stories based on true historical events.'))
        cat_scary = story_time_service.get_category_by_id(category_id=cat_scary_id)
        cat_funny = story_time_service.get_category_by_id(category_id=cat_funny_id)
        cat_animal = story_time_service.get_category_by_id(category_id=cat_animal_id)
        cat_musical = story_time_service.get_category_by_id(category_id=cat_musical_id)
        cat_history = story_time_service.get_category_by_id(category_id=cat_history_id)
        num_rows_created = db_session.query(Category).count()
        print('Created {} categories'.format(num_rows_created))

        # Stories
        story_zoo = Story(title='Animal Escape', description='See how all the animals escape from the zoo!',
                          story_text='<REPLACE>',
                          active=True, user_id=user_1,
                          categories=[cat_funny, cat_animal])
        story_zoo_id = story_time_service.create_story(story_zoo)
        story_fresh = Story(title='Fresh Prince', description='A tune from the prince himself!',
                            story_text='<REPLACE>',
                            active=True, user_id=user_2, categories=[cat_funny, cat_musical])
        story_fresh_id = story_time_service.create_story(story_fresh)
        story_wolf = Story(title='The Big Bad Wolf', description='A story about a scary wolf in the woods!',
                           story_text='<REPLACE>',
                           active=True, user_id=user_1, categories=[cat_scary])
        story_wolf_id = story_time_service.create_story(story_wolf)
        story_tj = Story(title='Americans vs Pirates',
                         description='A story about the young American country''s fight with the Tripoli pirates.',
                         story_text='<REPLACE>',
                         active=True, user_id=user_3, categories=[cat_history])
        story_tj_id = story_time_service.create_story(story_tj)
        story_bf = Story(title='Benjamin Franklin',
                         description='A not so well known story about one of America''s founding fathers, Benjamin Franklin.',
                         story_text='<REPLACE>',
                         active=True, user_id=user_3, categories=[cat_history])
        story_bf_id = story_time_service.create_story(story_bf)

        # Update story text for each story from lipsum generator (every second so we don't hit server too hard)
        url = 'https://lipsum.com/feed/json?what=paras&amount=5&start=yes'
        for story in story_time_service.get_stories():
            h = httplib2.Http()
            json_result = json.loads(h.request(url, 'GET')[1])
            story.story_text = json_result['feed']['lipsum']
            db_session.add(story)
            db_session.commit()
            time.sleep(1)

        num_rows_created = db_session.query(Story).count()
        print('Created {} stories'.format(num_rows_created))

        db_session.commit()
    except Exception as exc:
        print('Error creating test data:')
        print(exc)
        db_session.rollback()


if __name__ == '__main__':
    delete_and_recreate_test_data()
