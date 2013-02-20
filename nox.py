from flask import Flask
from flask.ext.assets import Bundle, Environment
from redis import StrictRedis


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('settings.cfg')
    app.config.from_pyfile('local_settings.cfg', silent=True)

    app.redis = StrictRedis(db=app.config['REDIS_DB'])

    assets = Environment(app)
    assets.config['stylus_plugins'] = ['nib']
    assets.config['stylus_extra_args'] = ['--inline', '--include', 'static']
    assets.register(
        'css',
        '../styles/normalize.styl',
        '../styles/screen.styl',
        filters='stylus,cssmin', output='gen/screen.css')
    assets.register(
        'pinmeal',
        'vendor/jquery-1.8.2.js',
        'vendor/underscore.js',
        'vendor/backbone.js',
        'vendor/handlebars.runtime-1.0.rc.1.js',
        Bundle(
            '../scripts/spot*.handlebars',
            depends='dummy',  # to work around a webassets caching bug
            filters='handlebars', output='gen/pinmeal-handlebars.js'),
        Bundle(
            '../scripts/pinmeal.coffee',
            filters='coffeescript', output='gen/pinmeal-coffee.js'),
        filters='uglifyjs', output='gen/pinmeal.js')

    from main import main
    app.register_blueprint(main)
    #from pinmeal import pinmeal
    #app.register_blueprint(pinmeal, url_prefix='/pinmeal')

    return app
