from flask import current_app as app
from uwsgidecorators import timer

from media import CollectLatestMedia


@timer(1800)
def update_instagram():
    c = CollectLatestMedia()
    c.run(app)
