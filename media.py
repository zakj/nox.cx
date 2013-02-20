import calendar

from instagram.client import InstagramAPI
from flask.ext.script import Command


class CollectLatestMedia(Command):
    """Collects the latest Instagram images."""

    def handle(self, app):
        return self.run(app)

    def run(self, app):
        api = InstagramAPI(access_token=app.config['INSTAGRAM_ACCESS_TOKEN'])
        user_id = app.config['INSTAGRAM_USER_ID']
        media, _next = api.user_recent_media(user_id=user_id, count=10)
        p = app.redis.pipeline(transaction=False)
        for item in media:
            p.hmset('instagram:media:%s' % item.id, dict(
                thumbnail=item.images['thumbnail'].url,
                link=item.link,
            ))
            score = calendar.timegm(item.created_time.timetuple())
            p.zadd('instagram:user:%s:media' % user_id, score, item.id)
        p.execute()
