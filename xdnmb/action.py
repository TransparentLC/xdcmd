import xdnmb.api
import xdnmb.model
import xdnmb.globals
import xdnmb.util

def loadForumGroup():
    xdnmb.globals.forumGroups = [
        xdnmb.model.ForumGroup(
            gid=0,
            sort=0,
            name='时间线',
            forums=xdnmb.api.getTimelineList(),
        )
    ]
    forumGroups = xdnmb.api.getForumList()
    xdnmb.globals.forumGroups.extend(forumGroups)
    xdnmb.globals.forums = sum((list(forumGroup.forums) for forumGroup in forumGroups), [])

@xdnmb.util.floatAlertExceptionCatch
def loadForum(forum: xdnmb.model.Forum, page: int = 1):
    xdnmb.globals.forumThreads = xdnmb.api.getForum(forum, page)
    xdnmb.globals.forum = forum
    xdnmb.globals.forumPage = page
    xdnmb.globals.thread = None
    xdnmb.globals.threadPage = None
    xdnmb.globals.forumContentControl.vertical_scroll = 0
    xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

@xdnmb.util.floatAlertExceptionCatch
def loadThread(thread: xdnmb.model.Thread, page: int = 1):
    xdnmb.globals.thread = xdnmb.api.getThread(thread, page)
    xdnmb.globals.threadPage = page
    xdnmb.globals.forumContentControl.vertical_scroll = 0
    xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)
