import sqlite3
import pickle
import random
import datetime


def create(conn): #expects sqlite3 connection

    # get movie data generated with scrape.py
    # This data is real
    # has (title,director,year,date (full release date), rating (user rating at themoviedatabase.org), poster (image url), overview (movie description))
    with open('gen/movies') as f:
        movies = pickle.load(f)

    # get reviewer name list
    # These names are fake, though the ratings are biased around the actual rating
    with open('gen/names') as f:
        names = f.read().splitlines()

    # Grab create sql from files. Normally, I would embed it, but this is easier to read.
    with open('gen/drop.sql') as f:
        dropsql = f.read()
    with open('gen/create.sql') as f:
        createsql = f.read()

    try:
        conn.executescript(dropsql)
        print "Tables dropped"
    except sqlite3.OperationalError:
        print "Tables don't exist so not dropping them"

    try:
        conn.executescript(createsql)
        print "Tables created"
    except:
        print "Unable to create tables"

    try:
        # executes the following line for every object in movies
        conn.executemany("insert into movie (title,director,year,poster,overview) values (:title, :director, :year, :poster,:overview);",movies)
        print "Movie data inserted"
    except:
        print "Unable to insert movie data"

    try:
        # executes the following line for every name in list
        conn.executemany("insert into reviewer (name) values (?);",[(x,) for x in names])
        print "Reviewer data inserted"
    except:
        print "Unable to insert reviewer data"

    try:
        # make sure some have no rating
        moviesSkipped = random.sample(xrange(0,len(movies)),random.randint(12,25))

        # for each reviewer... (by index)
        for reviewer in xrange(len(names)):
            # get random sample of movies
            moviesReviewed = random.sample(xrange(0,len(movies)),random.randint(75,125))

            # for each movie... (by index)
            for movie in moviesReviewed:
                if movie in moviesSkipped:
                    continue
                # get randomized rating biased toward real rating (scaled to 5 star system)
                rating = int(round(movies[movie]['rating'] / 2.0 + random.randint(-1,1)))
                # make sure rating is in [0,5]
                if rating < 0:
                    rating = 0
                elif rating > 5:
                    rating = 5
                # get random date within 90 days of release
                ratingDate = movies[movie]['date'] + datetime.timedelta(random.randint(0,90))
                conn.execute("insert into rating (movieID,reviewerID,stars,ratingDate) values (?,?,?,?);",(movie,reviewer,rating,ratingDate))
        print "Rating data inserted"
    except IndexError:
        print "Unable to insert rating data"

    # push data into database
    conn.commit()

def get_best_worst(conn,order,year=False):
    # get 10 best or worst movies (chosen by order), optionally by year
    if year:
        return conn.execute('select first.movieID as movieID,title,poster,stars,votes from \
            (select movieID,avg(stars) as stars,count(stars) as votes from rating group by movieID order by stars {0}) first \
            join (select movieID,title,poster from movie where year = ?) second \
            on first.movieID = second.movieID limit 10;'.format(order),(year,))
    else:
        return conn.execute('select first.movieID as movieID,title,poster,stars,votes from \
            (select movieID,avg(stars) as stars,count(stars) as votes from rating group by movieID order by stars {0} limit 10) first \
            join (select movieID,title,poster from movie) second \
            on first.movieID = second.movieID;'.format(order))

def get_random(conn):
    # get 10 random movies
    return conn.execute('select first.movieID as movieID,title,poster,stars,votes from \
        (select movieID,title,poster from movie order by random() limit 10) first \
        join (select movieID,avg(stars) as stars,count(stars) as votes from rating group by movieID) second \
        on first.movieID = second.movieID;')

def get_none(conn,page):
    # returns movie rows that have no rating associated; Grab 11 so we know if there should be another page
    return conn.execute('select movieID,title,poster,0 as stars,0 as votes from movie where movieID not in \
        (select movieID from rating) limit 11 offset ?;',((page-1)*10,))

def get_search(conn,page,search):
    # returns movie rows with title like search; Grab 11 so we know if there should be another page
    return conn.execute('select first.movieID as movieID,title,poster,stars,votes from \
            (select movieID,title,poster from movie where title like ?) first \
        join (select movieID,avg(stars) as stars,count(stars) as votes from rating group by movieID) second \
        on first.movieID = second.movieID limit 11 offset ?;',('%'+search+'%',(page-1)*10))

def get_movie(conn,movieID):
    # returns movie info
    return conn.execute('select * from (select * from movie where movieID = ?) first \
        left join (select movieID as ID,avg(stars) as stars,count(stars) as votes from rating group by movieID) second \
        on first.movieID = second.ID;',(movieID,)).fetchone()

def get_reviews_by_movie(conn,movieID):
    # returns reviews on movie
    return conn.execute('select * from (select reviewerID as ID,stars from rating where movieID = ?) first \
        join reviewer on first.ID = reviewer.reviewerID;',(movieID,))

def get_reviewer(conn,reviewerID):
    # returns reviewer info
    return conn.execute('select * from (select * from reviewer where reviewerID = ?) first \
        left join (select reviewerID as ID,avg(stars) as stars,count(stars) as votes from rating group by reviewerID) second \
        on first.reviewerID = second.ID;',(reviewerID,)).fetchone()

def get_reviews_by_reviewer(conn,reviewerID):
    # returns reviews on movie
    return conn.execute('select movie.movieID as movieID,title,poster,stars from \
            movie join rating on movie.movieID = rating.movieID where reviewerID = ?;',(reviewerID,))

def get_years(conn):
    return [x[0] for x in conn.execute('select year from movie group by year;').fetchall()]
