from flask import Flask
from flask.ext.assets import Environment
from redis import StrictRedis


## create_app()  #############################################################

app = Flask(__name__)
app.config.from_pyfile('settings.cfg')
app.config.from_pyfile('local_settings.cfg', silent=True)

redis = StrictRedis(db=app.config['REDIS_DB'])

#import views
#app.register_blueprint(views)

assets = Environment(app)
assets.config['stylus_plugins'] = ['nib']
assets.config['stylus_extra_args'] = ['--inline', '--include', 'static']
assets.register(
    'css',
    '../styles/normalize.styl',
    '../styles/screen.styl',
    filters='stylus,cssmin', output='gen/screen.css')

def create_app():
    return app


## views.py  #################################################################

from flask import redirect, render_template, url_for


@app.route('/')
def index():
    return redirect(url_for('zakj'))

@app.route('/zakj')
def zakj():
    user_id = app.config['INSTAGRAM_USER_ID']
    ids = redis.zrevrange('instagram:user:%s:media' % user_id, 0, 5)
    p = redis.pipeline(transaction=False)
    for _id in ids:
        p.hgetall('instagram:media:%s' % _id)
    images = p.execute()
    return render_template('zakj.html', images=images)

@app.route('/sleep')
def sleep():
    return render_template('sleep.html')
