import dataclasses
import functools
import os
import requests
import secrets
import mimetypes
import xdnmb.globals
import xdnmb.model
import xdnmb.util

from bs4 import BeautifulSoup
from urllib.parse import urljoin

try:
    import orjson
    __import__('requests.models').Response.json = functools.cache(lambda self, **kwargs: orjson.loads(self.content))
except ImportError:
    pass

JSON_API_ENDPOINT = 'https://api.nmb.best/api/'
HTML_API_ENDPOINT = 'https://www.nmbxd.com/home/forum/'

def responseHook(r: requests.Response, *args, **kwargs):
    r.raise_for_status()
    if 'application/json' in r.headers['Content-Type']:
        d = r.json()
        if isinstance(d, dict) and 'success' in d and 'error' in d and not d['success']:
            raise Exception(d['error'])

session = requests.Session()
session.request = functools.partial(session.request, timeout=5)
session.hooks['response'].append(responseHook)

CDN_PATH: str = ''

# https://github.com/seven332/Nimingban/blob/master/app/src/main/java/com/hippo/nimingban/client/ac/ACUrl.java

def getCDNPath() -> str:
    # https://image.nmb.best/
    return max(session.get(urljoin(JSON_API_ENDPOINT, 'getCDNPath')).json(), key=lambda e: e['rate'])['url']

def getForumList() -> tuple[xdnmb.model.ForumGroup, ...]:
    r = session.get(urljoin(JSON_API_ENDPOINT, 'getForumList'))

    groups: list[xdnmb.model.ForumGroup] = []
    for groupRaw in r.json():
        forums: list[xdnmb.model.Forum] = []
        for forumRaw in groupRaw['forums']:
            if int(forumRaw['id']) < 0:
                continue
            for k in ('showName', 'msg'):
                if k not in forumRaw:
                    forumRaw[k] = ''
            for k in ('sort', 'thread_count'):
                if k not in forumRaw:
                    forumRaw[k] = 0
            forums.append(xdnmb.model.Forum(
                fid=int(forumRaw['id']),
                sort=int(forumRaw['sort']),
                name=forumRaw['showName'] or forumRaw['name'],
                notice=xdnmb.util.stripHTML(forumRaw['msg']),
                threadCount=int(forumRaw['thread_count']),
            ))
        forums.sort(key=lambda e: e.sort)
        groups.append(xdnmb.model.ForumGroup(
            gid=int(groupRaw['id']),
            sort=int(groupRaw['sort']),
            name=groupRaw['name'],
            forums=tuple(forums),
        ))
    return tuple(groups)

def getTimelineList() -> tuple[xdnmb.model.Timeline, ...]:
    r = session.get(urljoin(JSON_API_ENDPOINT, 'getTimelineList'))

    timelines: list[xdnmb.model.Timeline] = []
    for timelineRaw in r.json():
        timelines.append(xdnmb.model.Timeline(
            fid=timelineRaw['id'],
            name=timelineRaw['display_name'] or timelineRaw['name'],
            notice=xdnmb.util.stripHTML(timelineRaw['notice']),
            maxPage=timelineRaw['max_page']
        ))
    return tuple(timelines)

def getForum(forum: xdnmb.model.Forum|xdnmb.model.Timeline, page: int = 1) -> tuple[xdnmb.model.Thread, ...]:
    c = {
        xdnmb.model.Forum: 'showf',
        xdnmb.model.Timeline: 'timeline',
    }[type(forum)]
    r = session.get(urljoin(JSON_API_ENDPOINT, c), params={
        'id': forum.fid,
        'page': page,
    })
    threads: list[xdnmb.model.Thread] = []
    for threadRaw in r.json():
        threads.append(xdnmb.model.Thread(
            tid=threadRaw['id'],
            replyCount=threadRaw['ReplyCount'],
            img=(
                (CDN_PATH + 'image/' + threadRaw['img'] + threadRaw['ext'])
                if threadRaw['img'] and threadRaw['ext']
                else None
            ),
            imgThumb=(
                (CDN_PATH + 'thumb/' + threadRaw['img'] + threadRaw['ext'])
                if threadRaw['img'] and threadRaw['ext']
                else None
            ),
            now=xdnmb.util.parseThreadTime(threadRaw['now']),
            userHash=threadRaw['user_hash'],
            name=threadRaw['name'],
            title=threadRaw['title'],
            content=xdnmb.util.stripHTML(threadRaw['content']),
            sage=bool(threadRaw['sage']),
            admin=bool(threadRaw['admin']),
            forum=next(
                (forum for forum in xdnmb.globals.forums if forum.fid == threadRaw['fid']),
                None,
            ),
            isPo=False,
        ))
    return tuple(threads)

def getThread(thread: xdnmb.model.Thread, page: int = 1) -> xdnmb.model.Thread:
    r = session.get(urljoin(JSON_API_ENDPOINT, 'thread'), params={
        'id': thread.tid,
        'page': page,
    })
    thread = dataclasses.replace(thread)
    thread.replyCount = r.json()['ReplyCount']
    thread.replies = []
    for replyRaw in r.json()['Replies']:
        thread.replies.append(xdnmb.model.Reply(
            tid=replyRaw['id'],
            img=(
                (CDN_PATH + 'image/' + replyRaw['img'] + replyRaw['ext'])
                if replyRaw['img'] and replyRaw['ext']
                else None
            ),
            imgThumb=(
                (CDN_PATH + 'thumb/' + replyRaw['img'] + replyRaw['ext'])
                if replyRaw['img'] and replyRaw['ext']
                else None
            ),
            now=xdnmb.util.parseThreadTime(replyRaw['now']),
            userHash=replyRaw['user_hash'],
            name=replyRaw['name'],
            title=replyRaw['title'],
            content=xdnmb.util.stripHTML(replyRaw['content']),
            admin=bool(replyRaw['admin']),
            isPo=replyRaw['user_hash'] == thread.userHash,
        ))
    thread.replies = tuple(thread.replies)
    return thread

@functools.lru_cache(1024)
def getReference(tid: int) -> xdnmb.model.Reply:
    r = session.get(urljoin(HTML_API_ENDPOINT, 'ref'), params={
        'id': tid,
    })
    soup = BeautifulSoup(r.text, features='lxml')
    if not soup.select_one('.h-threads-item-reply.h-threads-item-ref[data-threads-id]').attrs['data-threads-id']:
        raise Exception('引用的串号不存在')
    imgNode = soup.select_one('.h-threads-img-a')
    if imgNode:
        img = imgNode.attrs['href']
    else:
        img = None
    imgThumbNode = soup.select_one('.h-threads-img-a > img.h-threads-img')
    if imgThumbNode:
        imgThumb = imgThumbNode.attrs['src']
    else:
        imgThumb = None
    now = xdnmb.util.parseThreadTime(soup.select_one('.h-threads-info-createdat').text)
    userHash = xdnmb.util.stripHTML(soup.select_one('.h-threads-info-uid')).removeprefix('ID:')
    name = xdnmb.util.stripHTML(soup.select_one('.h-threads-info-email'))
    title = xdnmb.util.stripHTML(soup.select_one('.h-threads-info-title'))
    content = xdnmb.util.stripHTML(soup.select_one('.h-threads-content'))
    admin = bool(soup.select_one('.h-threads-info-uid > font[color="red"]'))
    return xdnmb.model.Reply(
        tid=tid,
        img=img,
        imgThumb=imgThumb,
        now=now,
        userHash=userHash,
        name=name,
        title=title,
        content=content,
        admin=admin,
        isPo=False,
    )

def postThread(
    forumOrThread: xdnmb.model.Forum|xdnmb.model.Thread,
    name: str,
    title: str,
    content: str,
    image: str|None,
    water: bool,
):
    c = {
        xdnmb.model.Forum: 'doPostThread.html',
        xdnmb.model.Thread: 'doReplyThread.html',
    }[type(forumOrThread)]
    f = {
        'name': (None, name),
        'title': (None, title),
        'content': (None, content),
    }
    if isinstance(forumOrThread, xdnmb.model.Forum):
        f['fid'] = (None, forumOrThread.fid)
    elif isinstance(forumOrThread, xdnmb.model.Thread):
        f['resto'] = (None, forumOrThread.tid)
    if image:
        if image in xdnmb.globals.STICKERS:
            image = xdnmb.globals.STICKERS[image]
        f['image'] = (
            secrets.token_urlsafe(12) + os.path.splitext(image.split('?')[0])[1],
            (
                session.get(image, stream=True).raw
                if image.startswith('https://') or image.startswith('http://') else
                open(image, 'rb')
            ),
            mimetypes.guess_type(image.split('?')[0])[0],
        )
        if water:
            f['water'] = (None, 'true')
    r = session.post(urljoin(HTML_API_ENDPOINT, c), files=f)
    soup = BeautifulSoup(r.text, features='lxml')
    errorNode = soup.select_one('.error')
    if errorNode:
        raise Exception(xdnmb.util.stripHTML(errorNode))
