import sys
from mycroft import MycroftSkill, intent_handler # type: ignore
sys.path.append("/usr/lib/UBUVoiceAssistant")
from UBUVoiceAssistant.model.discussion import Discussion # type: ignore
from UBUVoiceAssistant.model.forum import Forum # type: ignore
from UBUVoiceAssistant.util import util # type: ignore


class UbuCourseSkill(MycroftSkill):

    def __init__(self):
        super().__init__()
        self.learning = True

    def initialize(self):
        self.ws = util.get_data_from_server()

    @intent_handler('CourseForums.intent')
    def handle_course_forums(self, message):
        course_name = message.data['course']
        course_id = util.get_course_id_by_name(course_name, self.ws.get_user_courses())
        if course_id:
            course = self.ws.get_user().get_course(course_id)
            forums = course.get_forums()
            # If the user has never looked the course forums up
            if not forums:
                self.load_forums(course)
                forums = course.get_forums()

            self.speak_dialog('forums', data={'course': course_name}, wait=True)
            chosen_forum = self.read_forums(forums)
            if not chosen_forum:
                self.speak_dialog('select.forum')
                return

            self.speak_dialog('discussions', data={'forum': chosen_forum.get_name()}, wait=True)
            chosen_discussion = self.read_discussions(chosen_forum.get_discussions())
            if not chosen_discussion:
                self.speak_dialog('select.discussion')
                return

            posts = self.ws.get_forum_discussion_posts(str(chosen_discussion.get_id()))
            self.read_posts(posts)

        else:
            self.speak_dialog('no.course')

    def load_forums(self, course):
        forums = self.ws.get_course_forums(course.get_id())
        course_forums = []
        for forum in forums:
            forum_discussions = []
            discussions = self.ws.get_forum_discussions(str(forum['id']))
            for discussion in discussions['discussions']:
                forum_discussions.append(Discussion(discussion))
            course_forums.append(Forum(forum, forum_discussions))
        course.set_forums(course_forums)

    def read_forums(self, forums):
        for forum in forums:
            self.speak(forum.get_name(), wait=True)
            resp = self.get_response(dialog='forum.discussions')
            if resp.lower() in ('si', 'sí', 'yes'):
                return forum
        return None

    def read_discussions(self, discussions):
        for discussion in discussions:
            self.speak(discussion.get_name(), wait=True)
            resp = self.get_response(dialog='discussion.posts')
            if resp.lower() in ('si', 'sí', 'yes'):
                return discussion
        return None

    def read_posts(self, posts):
        complete = self.get_response(dialog='whole.discussion')
        if complete.lower() in ('si', 'sí', 'yes'):
            discussion = []
            for post in reversed(posts['posts']):
                discussion.append(post['userfullname'] + ': ' + post['message'])
            self.speak(str(discussion).strip("[]'"))
        else:
            for post in reversed(posts['posts']):
                resp = self.get_response(dialog='next.post')
                if resp.lower() == 'no':
                    break
                self.speak(post['userfullname'] + ': ' + post['message'])


def create_skill():
    return UbuCourseSkill()
