from uwsgidecorators import timer

from media import CollectLatestMedia
from nox import create_app


@timer(1800)
def update_instagram(signum):
    c = CollectLatestMedia()
    c.run(create_app())
