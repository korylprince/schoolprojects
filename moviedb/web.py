import sqlite3
import db
import re
import urlparse

def application(env, start_response):
    #main handler called every request
    url = env['PATH_INFO']
    content = mapper(url,env,start_response)
    # if not returning normally, let function handle output
    if content is None:
        return
    # otherwise put everything in the template
    return templates['main'].format(**content).encode('utf-8')

def mapper(url,env,start_response):
#maps given urls to functions
    #remove trailing /
    if url[-1] == '/' and len(url) != 1:
        url = url[:-1]
    parsed = url_match.match(url)
    if parsed is None or parsed.groupdict() is None:
        return url_404(start_response)
    else:
        # reassemble url and check in map
        params = parsed.groupdict()
        paramlist = [x for x in [params['func'],'#' if params['num'] else None,params['sub']] if x is not None]
        url = '/'+'/'.join(paramlist)
        if url in path_map:
            # call function with parameters
            func = path_map[url][:] #use copy
            if '#' in func:
                func[func.index('#')] = int(params['num'])
            if 'get' in func:
                func[func.index('get')] = urlparse.parse_qs(env['QUERY_STRING'])
            response, content = func[0](*func[1:])
            start_response(*response)
            return content 
        else:
            return url_404(start_response)

##
## url functions
##

def url_404(start_response):
    start_response('404 Not Found', [('Content-Type','text/html')])
    return {'title':u'Oops','content':templates['not_found']}

def url_index():
#/ -> index with search, links, and featured movies (3 highest rated)
    return (('200 OK', [('Content-Type','text/html')]),{u'title':u'Welcome','content':templates['index']})

def url_best(year=False):
#/best -> 10 best of all time
#/best/<year> -> 10 best of year
    out = ['{0}<h4>Select by year:</h4><span class="yearwrapper">'.format('<h4>Showing {0}</h4>'.format(year) if year else '')]
    for y in db.get_years(conn):
        out.append('<a href="/best/{0}">{0}</a> '.format(y))
    out.append('<a href="/best">All</a></span>')
    movielist = movie_list_gen(db.get_best_worst(conn,'desc',year))
    if movielist == []:
        return (('404 Not Found', [('Content-Type','text/html')]),{'title':u'Oops','content':templates['not_found']})
    out += movielist
    return (('200 OK', [('Content-Type','text/html')]),{'title':u'Best Movies of ' + (unicode(year) if year else u'All Time'),'content':u''.join(out)})

def url_worst(year=False):
#/worst -> 10 worst of all time
#/worst/<year> -> 10 worst of year
    out = ['{0}<h4>Select by year:</h4><span class="yearwrapper">'.format('<h4>Showing {0}</h4>'.format(year) if year else '')]
    for y in db.get_years(conn):
        out.append('<a href="/worst/{0}">{0}</a> '.format(y))
    out.append('<a href="/worst">All</a></span>')
    movielist = movie_list_gen(db.get_best_worst(conn,'asc',year))
    if movielist == []:
        return (('404 Not Found', [('Content-Type','text/html')]),{'title':u'Oops','content':templates['not_found']})
    out += movielist
    return (('200 OK', [('Content-Type','text/html')]),{'title':u'Worst Movies of ' + (unicode(year) if year else u'All Time'),'content':u''.join(out)})

def url_random():
#/random -> 10 random movies
    out = movie_list_gen(db.get_random(conn))
    return (('200 OK', [('Content-Type','text/html')]),{'title':u'Random','content':u''.join(out)})

def url_none(page):
#/none/<page> -> movies with no rating with paging
    rows = db.get_none(conn,page)
    flags = []
    out = movie_list_gen(rows,flags)
    if out == []:
        return (('404 Not Found', [('Content-Type','text/html')]),{'title':u'Oops','content':templates['not_found']})
    out.append(pager_gen('none',page,'more' in flags))
    return (('200 OK', [('Content-Type','text/html')]),{'title':u'Not Rated','content':u''.join(out)})

def url_search(query,page):
#/search/<num> -> search based on post data with paging
    try:
        search = query['s'][0]
        rows = db.get_search(conn,page,search)
    except KeyError, IndexError:
        return (('400 Bad Request', [('Content-Type','text/html')]),{'title':u'Oops','content':templates['bad_request']})
    flags = []
    out = movie_list_gen(rows,flags)
    if out == []:
        out = ['<span class="error">Aw, Man.</span><p class="error_text">Nothing turned up. You can always <a href="/">try something else</a>...</p>']
    else:
        out.append(pager_gen('search',page,'more' in flags,'?s='+search))
    return (('200 OK', [('Content-Type','text/html')]),{'title':u'Searching: '+search,'content':u''.join(out)})

def url_movie(movieID):
#/movie/<num> -> movie page
    row = db.get_movie(conn,movieID)
    if row is None:
        return (('404 Not Found', [('Content-Type','text/html')]),{'title':u'Oops','content':templates['not_found']})
    row = dict(row)
    row['stars'] = star_gen(row['stars'],row['votes'])
    row['reviews'] = reviewer_list_slim_gen(db.get_reviews_by_movie(conn,movieID))
    out = templates['movie_full'].format(**row)
    return (('200 OK', [('Content-Type','text/html')]),{'title':row['title'],'content':out})

def url_reviewer(reviewerID):
#/reviewer/<num> -> reviewer page
    row = db.get_reviewer(conn,reviewerID)
    if row is None:
        return (('404 Not Found', [('Content-Type','text/html')]),{'title':u'Oops','content':templates['not_found']})
    row = dict(row)
    row['stars'] = star_gen(row['stars'],row['votes'])
    row['color'] = color_gen(row['name'])
    row['reviews'] = movie_list_slim_gen(db.get_reviews_by_reviewer(conn,reviewerID))
    out = templates['reviewer_full'].format(**row)
    return (('200 OK', [('Content-Type','text/html')]),{'title':row['name'],'content':out})

def url_redirect(url):
    return (('302 Found', [('Location',url),('Content-Type','text/html')]),None)

##
##  Helper Functions
##

def movie_list_gen(cursor,flags = None):
#generate list of movies
    out = []
    count = 0
    for row in cursor:
        # check if there's another page
        if count >= 10:
            if flags is not None:
                flags.append('more')
            return out
        count += 1
        row = dict(row)
        row['stars'] = star_gen(row['stars'],row['votes'])
        out.append(templates['movie_brief'].format(**row))
    return out

def movie_list_slim_gen(cursor):
#generate list of reviews
    out = []
    for row in cursor:
        row = dict(row)
        row['stars'] = star_gen_single(row['stars'])
        out.append(templates['movie_slim'].format(**row))
    return u''.join(out)

def reviewer_list_slim_gen(cursor):
#generate list of reviews
    out = []
    for row in cursor:
        row = dict(row)
        row['stars'] = star_gen_single(row['stars'])
        row['color'] = color_gen(row['name'])
        out.append(templates['reviewer_slim'].format(**row))
    return u''.join(out)

def pager_gen(func,page,more,query=''):
# generates pager navigation
    out = ['<nav class="pager">']
    if page > 1:
        out.append('<a class="pager_left" href="/{0}/{1}{2}">&larr; Previous</a>'.format(func,page-1,query))
    if more:
        out.append('<a class="pager_right" href="/{0}/{1}{2}">Next &rarr;</a>'.format(func,page+1,query))
    out.append('</nav>')
    return u''.join(out)

def star_gen(rating, votes):
#generate star output based on rating and votes
    if rating is None:
        rating = 0
        votes = 0
    out = ['<div title="Average Rating: {0}">'.format(round(rating,2))]
    rating = int(round(rating))
    for star in range(5):
        if star < rating:
            out.append('<span class="star"></span>')
        else:
            out.append('<span class="nostar"></span>')
    out.append(' <span class="votes">Votes: {0}</span></div>'.format(votes))
    return u''.join(out)

def star_gen_single(rating):
#generate star output based on single rating 
    if rating is None:
        rating = 0
    out = ['<div>']
    rating = int(round(rating))
    for star in range(5):
        if star < rating:
            out.append('<span class="star"></span>')
        else:
            out.append('<span class="nostar"></span>')
    out.append('</div>')
    return u''.join(out)

def color_gen(name):
    #generates random color based on name
    c = hex(hash(name))
    if len(c) < 8:
        return '#'+c[2:]+'f'*(8-len(c))
    return '#' + c[-6:]

##
## Performed Every Restart
##
     
# connect to database and generate it
conn = sqlite3.connect('ratings.db')
conn.row_factory = sqlite3.Row
db.create(conn)

# read template files
templates = {}
with open('templates/main.html') as f:
    templates['main'] = unicode(f.read())
with open('templates/index.html') as f:
    templates['index'] = unicode(f.read())
with open('templates/movie_full.html') as f:
    templates['movie_full'] = unicode(f.read())
with open('templates/movie_brief.html') as f:
    templates['movie_brief'] = unicode(f.read())
with open('templates/movie_slim.html') as f:
    templates['movie_slim'] = unicode(f.read())
with open('templates/reviewer_full.html') as f:
    templates['reviewer_full'] = unicode(f.read())
with open('templates/reviewer_slim.html') as f:
    templates['reviewer_slim'] = unicode(f.read())
with open('templates/400.html') as f:
    templates['bad_request'] = unicode(f.read())
with open('templates/404.html') as f:
    templates['not_found'] = unicode(f.read())

# define urls
path_map = {
    '/' : [url_index],
    '/best' : [url_best],
    '/best/#' : [url_best,'#'],
    '/worst' : [url_worst],
    '/worst/#' : [url_worst,'#'],
    '/random' : [url_random],
    '/none' : [url_redirect,'/none/1'],
    '/none/#' : [url_none,'#'],
    '/search' : [url_redirect,'/'],
    '/search/#' : [url_search,'get','#'],
    '/movie' : [url_redirect,'/'],
    '/movie/#' : [url_movie,'#'],
    '/reviewer' : [url_redirect,'/'],
    '/reviewer/#' : [url_reviewer,'#']
}

#compile regex
url_match = re.compile("/(?:(?P<func>[a-z]+)(?:/(?P<num>[1-9][0-9]*)(?:/(?P<sub>[a-z]+))?)?)?$")
