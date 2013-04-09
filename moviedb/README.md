The Movie Database
<https://github.com/korylprince/schoolprojects/tree/master/moviedb>

A uWSGI application that acts as a frontend to a movie database.
#Usage#

Included is a uwsgi .ini file and an nginx configuration for setup.

gen/scrape.py is used to get data from TMDB (You will need an api key.) This needs <https://github.com/wagnerrp/pytmdb3>.

Starting the application without the data from that script at gen/movies will cause an error.

Much more info is included in the manual (required as part of the project.

#Copyright Information#
Copyright 2013 Kory Prince (korylprince AT gmail DAWT com).

License is the "Do Whatever You Want With It" License. Public Domain - whatever you want.

Included third party libraries have their own license.
