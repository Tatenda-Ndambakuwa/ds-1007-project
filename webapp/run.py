import tornado.ioloop 
import tornado.web
import signal, os
import pandas as pd
import numpy as np
from nbastats import rendering, utility
from nbastats.salaries_analysis import salaries_stats_analysis
from nbastats.salaries_analysis import salaries_preprocessing

# define some constants
YEARS = xrange(2000, 2015)
TEMPLATE_DIR = 'templates'

class OverviewHandler(tornado.web.RequestHandler):
    """ Request Handler for /overview/year """
    def get(self, year=2014):
        try:
            filename = 'nbastats/static/data/stats_{}.csv'.format(year)
            stats = pd.read_csv(filename)
        except IOError:
            print 'data not found'
            raise tornado.web.HTTPError(500)

        self.write(rendering.render_leaders(stats, 'all', 12, year, TEMPLATE_DIR, 'overview.html'))

class PositionHandler(tornado.web.RequestHandler):
    """ Request handler for /overview/year/position """
    def get(self, year, position):
        try:
            stats = pd.read_csv('nbastats/static/data/stats_{}.csv'.format(year))
        except IOError:
            print 'data not found'
            raise tornado.web.HTTPError(500)
        pos = position.upper()
        self.write(rendering.render_leaders(stats[stats.POS==pos], position, 8, year, TEMPLATE_DIR, 'overview.html'))

class PlayersListHandler(tornado.web.RequestHandler):
    """ Request handler for /players/name """
    def get(self, option, position):
        try:
            players = pd.read_csv('nbastats/static/data/players_{}.csv'.format(option))
        except IOError:
            raise tornado.web.HTTPError(500)
        
        self.write(rendering.render_players(players, position, option, TEMPLATE_DIR, 'players_index.html'))
        
class PlayersOverviewHandler(tornado.web.RequestHandler):
    """ """
    def get(self):
        position_counts = {}
        for year in YEARS:
            try:
                stats = pd.read_csv('nbastats/static/data/stats_{}.csv'.format(year))
            except IOError:
                continue
            position_counts[year] = utility.count_position(stats)
        self.write(rendering.render_league_info(position_counts, TEMPLATE_DIR, 'league_info.html'))

class PlayerHandler(tornado.web.RequestHandler):
    """ """
    def get(self, option, name):
        stats = pd.read_csv('nbastats/static/data/players_{}.csv'.format(option), index_col='PLAYER')
        player = utility.url_to_name(name)
        img_src = stats.ix[player]['IMG']
        if not img_src:
            img_src = None
        years = stats.ix[player]['YEARS'].strip().split()
        last_year = years[-1]
        stats = pd.read_csv('nbastats/static/data/stats_{}.csv'.format(last_year), index_col='PLAYER')
        self.write(rendering.render_player(player, stats.ix[[player]], years, last_year, option, img_src, TEMPLATE_DIR, 'player.html'))

class PlayerByYearHandler(tornado.web.RequestHandler):
    """ """
    def get(self, option, name, year):
        stats = pd.read_csv('nbastats/static/data/players_{}.csv'.format(option), index_col='PLAYER')
        player = utility.url_to_name(name)
        img_src = stats.ix[player]['IMG']
        years = stats.ix[player]['YEARS'].strip().split()
        stats = pd.read_csv('nbastats/static/data/stats_{}.csv'.format(year), index_col='PLAYER')
        self.write(rendering.render_player(player, stats.ix[[player]], years, year, option, img_src, TEMPLATE_DIR, 'player.html'))

class TrendHandler(tornado.web.RequestHandler):
    def get(self):
        oa = overall_analysis()
        pos = position_analysis()
        self.write(rendering.render_trend(oa, pos, TEMPLATE_DIR, 'salaries_trend.html'))
        
def make_app():
    settings = {"debug": True,
                "static_path": os.path.join(os.path.dirname(__file__), "nbastats/static"),}

    return tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, dict(path=settings['static_path'])),
        (r'/overview/(20[01][0-9])', OverviewHandler),
        (r'/overview/(20[01][0-9])/(c|pf|sf|sg|pg)', PositionHandler),
        (r'/players/(current|historic)/(c|pf|sf|sg|pg)', PlayersListHandler),
        (r'/overview', tornado.web.RedirectHandler, {'url': '/overview/2014'}),
        (r'/players/current', tornado.web.RedirectHandler, {'url': '/players/current/c'}),
        (r'/players/historic', tornado.web.RedirectHandler, {'url': '/players/historic/c'}),
        (r'/players/info', PlayersOverviewHandler),
        (r'/players/(current|historic)/(.*)/(20[01][0-9])', PlayerByYearHandler),
        (r'/players/(current|historic)/(.*)', PlayerHandler),
        (r'/salaries/trend', TrendHandler),
    ], **settings)

def on_shutdown():
    print 'Shutting down'
    tornado.ioloop.IOLoop.instance().stop()

def main():
    app = make_app()
    app.listen(8080)
    ioloop = tornado.ioloop.IOLoop.instance()
    signal.signal(signal.SIGINT, lambda sig, frame: ioloop.add_callback_from_signal(on_shutdown))
    ioloop.start()

if __name__ == '__main__':
    main()
