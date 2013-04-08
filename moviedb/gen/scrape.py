import tmdb3 as t # uses https://github.com/wagnerrp/pytmdb3
import pickle
import sys

t.set_key('YOUR API KEY')
b = t.searchMovie('a')
movies = []
for y in range(len(b)):
    try:
        sys.stdout.write(str(y)+',')
        x = b[y]
        # we want recent movies
        if x.releasedate.year < 1970:
            continue
        # and movies in English
        if 'English' not in [y.name for y in x.languages]:
            continue
        # and decent movies
        if x.releases['US'].certification not in [u'G',u'PG',u'PG-13']:
            continue
        movie = dict()
        movie['title'] = x.title
        movie['year'] = x.releasedate.year
        movie['date'] = x.releasedate
        movie['director'] = [y.name for y in x.crew if y.job == 'Director'][0] or 'Director Unknown'
        movie['poster'] = x.poster.geturl('w185')
        movie['rating'] = x.userrating
        movie['overview'] = x.overview
        movies.append(movie)
        print len(movies)
    except KeyboardInterrupt:
        break
    except:
        print 'Error on: ',x
    if len(movies) == 2500:
        break

#dump to pickle file
with open('movies','w') as f:
    pickle.dump(movies,f)
