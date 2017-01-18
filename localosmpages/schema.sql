drop table if exists users;
create table users (
	osmid integer primary key,
	display_name text);

drop table if exists messages;
create table messages (
	id integer primary key autoincrement,
	title text,
	body text,
	user integer,
	parent integer);
