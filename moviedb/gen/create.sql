create table movie (
    movieID integer primary key autoincrement,
    title varchar(100),
    director varchar(50),
    year decimal(4,0),
    poster varchar(100), /* Extra field for movie poster */
    overview text /* Extra Field for movie description */
);

create table reviewer (
    reviewerID integer primary key autoincrement,
    name varchar(50)
);

create table rating (
    movieID integer,
    reviewerID integer,
    ratingDate date,
    stars integer,
    primary key (movieID,reviewerID), /* While the relation is many to many, no reviewer will review a movie twice. Besides, I'm generating the data so I know this holds. */
    foreign key (movieID) references movie (movieID),
    foreign key (reviewerID) references reviewer (reviewerID)
);
