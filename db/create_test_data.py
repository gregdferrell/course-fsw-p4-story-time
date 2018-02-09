from storytime import story_service
from storytime.storytime_db_init import Category, Story, User, db_session

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

    # Create test data
    # Users
    user_gf_id = story_service.create_user(User(name='gregdferrell', email='gferrell20@gmail.com', active=True))
    user_gm_id = story_service.create_user(User(name='gregor mendel', email='gregormendel@email.com', active=True))
    num_rows_created = db_session.query(User).count()
    print('Created {} users'.format(num_rows_created))

    # Categories
    cat_scary_id = story_service.create_category(Category(label='Scary', description='Scary stories!'))
    cat_funny_id = story_service.create_category(Category(label='Funny', description='Funny stories!'))
    cat_animal_id = story_service.create_category(Category(label='Animals', description='Stories about animials!'))
    cat_musical_id = story_service.create_category(
        Category(label='Musical', description='Stories that can be sung to music!'))
    num_rows_created = db_session.query(Category).count()
    print('Created {} categories'.format(num_rows_created))
    cat_scary = story_service.get_category_by_id(category_id=cat_scary_id)
    cat_funny = story_service.get_category_by_id(category_id=cat_funny_id)
    cat_animal = story_service.get_category_by_id(category_id=cat_animal_id)
    cat_musical = story_service.get_category_by_id(category_id=cat_musical_id)

    # Stories
    story_zoo = Story(title='Animal Escape', description='See how all the animals escape from the zoo!',
                      story_text='Once upon a time, all the zoo animals got together and planned their escape. This is their story ...',
                      active=True, user_id=user_gf_id,
                      categories=[cat_funny, cat_animal])
    story_zoo_id = story_service.create_story(story_zoo)
    story_fresh = Story(title='Fresh Prince', description='A tune from the prince himself.!',
                        story_text='Now, this is a story all about how my life got flip-turned upside down ...',
                        active=True, user_id=user_gf_id, categories=[cat_funny, cat_musical])
    story_fresh_id = story_service.create_story(story_fresh)
    story_wolf = Story(title='The Big Bad Wolf', description='A story about a scary wolf in the woods.!',
                       story_text='One day, a few children were playing near the woods ...',
                       active=True, user_id=user_gf_id, categories=[cat_scary])
    story_wolf_id = story_service.create_story(story_wolf)

    num_rows_created = db_session.query(Story).count()
    print('Created {} stories'.format(num_rows_created))

    db_session.commit()


except Exception as exc:
    print('Error creating test data:')
    print(exc)
    db_session.rollback()
