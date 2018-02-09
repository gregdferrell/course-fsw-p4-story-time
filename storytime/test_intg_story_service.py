#
# Story Time App
# Integration tests for the story_time_service functions
#

from storytime import story_time_service


def test_get_stories_by_category_id():
    category_funny = story_time_service.get_category_by_label('Funny')
    stories = story_time_service.get_stories_by_category_id(category_funny.id)
    assert stories.count() == 2
    assert any(story.title == 'Fresh Prince' for story in stories)
    assert any(story.title == 'Animal Escape' for story in stories)
