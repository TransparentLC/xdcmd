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
        ),
        xdnmb.model.ForumGroup(
            gid=0,
            sort=0,
            name='订阅',
            forums=(
                xdnmb.model.Feed(),
            ),
        ),
    ]
    forumGroups = xdnmb.api.getForumList()
    xdnmb.globals.forumGroups.extend(forumGroups)
    xdnmb.globals.forums = sum((list(forumGroup.forums) for forumGroup in forumGroups), [])

@xdnmb.util.floatAlertExceptionCatch
def loadForum(forum: xdnmb.model.Forum|xdnmb.model.Timeline|xdnmb.model.Feed, page: int = 1):
    if isinstance(forum, xdnmb.model.Feed):
        forumThreads = xdnmb.api.getFeed(page)
    else:
        forumThreads = xdnmb.api.getForum(forum, page)
    if not forumThreads:
        if isinstance(forum, xdnmb.model.Feed):
            xdnmb.util.floatAlert('我真的……一条都没有了', '订阅列表是空的' if page == 1 else '你已经翻到了订阅列表的最后一页')
        else:
            xdnmb.util.floatAlert('我真的……一条都没有了', '你已经翻到了这个版面的最后一页')
        return
    xdnmb.globals.forumThreads = forumThreads
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
