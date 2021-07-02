"""Module for the ubu-course skill
"""
import sys
from mycroft import MycroftSkill, intent_handler  # type: ignore
from bs4 import BeautifulSoup
sys.path.append("/usr/lib/UBUVoiceAssistant")
from UBUVoiceAssistant.util import util  # type: ignore
from UBUVoiceAssistant.model.forum import Forum  # type: ignore
from UBUVoiceAssistant.model.discussion import Discussion  # type: ignore


class UbuCourseSkill(MycroftSkill):
    """ubu-course skill class"""

    def __init__(self):
        super().__init__()
        self.learning = True
        self.webservice = None

    def initialize(self):
        """Initializes the needed data
        """
        self.webservice = util.get_data_from_server()

    @intent_handler('CourseForums.intent')
    def handle_course_forums(self, message):
        """Starting point to read forums

        Args:
            message: Mycroft message data
        """
        course_name = message.data['course']
        course_id = util.get_course_id_by_name(
            course_name, self.webservice.get_user_courses())
        if course_id:
            course = self.webservice.get_user().get_course(course_id)
            forums = course.get_forums()
            # If the user has never looked the course forums up
            if not forums:
                self.load_forums(course)
                forums = course.get_forums()

            self.speak_dialog(
                'forums', data={'course': course_name}, wait=True)
            chosen_forum = self.read_forums(forums)
            if not chosen_forum:
                self.speak_dialog('select.forum')
                return

            self.speak_dialog('discussions', data={
                              'forum': chosen_forum.get_name()}, wait=True)
            chosen_discussion = self.read_discussions(
                chosen_forum.get_discussions())
            if not chosen_discussion:
                self.speak_dialog('select.discussion')
                return

            posts = self.webservice.get_forum_discussion_posts(
                str(chosen_discussion.get_id()))
            self.read_posts(posts)

        else:
            self.speak_dialog('no.course')

    def load_forums(self, course):
        """Loads forums from a Moodle course

        Args:
            course (Course): The Course object
        """
        forums = self.webservice.get_course_forums(course.get_id())
        course_forums = []
        for forum in forums:
            forum_discussions = []
            discussions = self.webservice.get_forum_discussions(str(forum['id']))
            for discussion in discussions['discussions']:
                forum_discussions.append(Discussion(discussion))
            course_forums.append(Forum(forum, forum_discussions))
        course.set_forums(course_forums)

    def read_forums(self, forums):
        """Loops over forums, reading them

        Args:
            forums (list[Forum]): A list of forum objects

        Returns:
            Forum or None: A Forum object if the user answered yes or None if not
        """
        for forum in forums:
            self.speak(forum.get_name(), wait=True)
            resp = self.get_response(dialog='forum.discussions')
            if resp.lower() in ('si', 'sí', 'yes'):
                return forum
        return None

    def read_discussions(self, discussions):
        """Loops over discussions, reading them

        Args:
            discussions (list[Discussion]): A list of discussions

        Returns:
            Discussion or None: A Discussion object if the user answered yes or None if not
        """
        for discussion in discussions:
            self.speak(discussion.get_name(), wait=True)
            resp = self.get_response(dialog='discussion.posts')
            if resp.lower() in ('si', 'sí', 'yes'):
                return discussion
        return None

    def read_posts(self, posts):
        """Reads the first or all the posts

        Args:
            posts (dict): JSON dictionary containing the posts
        """
        complete = self.get_response(dialog='whole.discussion')
        if complete.lower() in ('si', 'sí', 'yes'):
            discussion = []
            for post in reversed(posts['posts']):
                discussion.append(util.reorder_name(
                    post['userfullname']) + ' dice: ' + self.clean_text(post['message']))
            self.speak(str(discussion).strip("[]'"))
        else:
            for post in reversed(posts['posts']):
                resp = self.get_response(dialog='next.post')
                if resp.lower() == 'no':
                    break
                self.speak(util.reorder_name(
                    post['userfullname']) + ' dice: ' + self.clean_text(post['message']))

    def clean_text(self, text):
        """Removes all HTML tags from a text

        Args:
            text (str): The text with HTML tags

        Returns:
            str: The text without HTML tags
        """
        return BeautifulSoup(text, "html.parser").get_text()


def create_skill():
    """Returns the ubu-messages skill

    Returns:
        UbuCourseSkill: The skill to interact with Moodle forums
    """
    return UbuCourseSkill()
