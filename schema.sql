drop table if exists books;
create table books (
  id integer primary key autoincrement,
  title string not null,
  description text not null,
  finished integer,
  created datetime
);
