from flask import Blueprint
from flask import current_app as app, redirect, render_template, url_for

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return redirect(url_for('main.zakj'))


@main.route('/zakj')
def zakj():
    user_id = app.config['INSTAGRAM_USER_ID']
    ids = app.redis.zrevrange('instagram:user:%s:media' % user_id, 0, 5)
    p = app.redis.pipeline(transaction=False)
    for _id in ids:
        p.hgetall('instagram:media:%s' % _id)
    images = p.execute()
    return render_template('zakj.html', images=images)


@main.route('/sleep')
def sleep():
    return render_template('sleep.html')
