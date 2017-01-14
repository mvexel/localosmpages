drop table if exists users;
create table users (
  osmid integer primary key,
  display_name text not null,
  changeset_count integer not null,
  avatar_url text not null,
  account_created text not null,
  contributor_terms_agreed boolean not null,
  pd boolean not null,
  traces_count integer not null,
  blocks_received integer not null,
  blocks_active integer not null,
  languages text not null,
  messages_received int not null,
  messages_unread int not null,
  messages_sent int not null,
  join_date datetime not null,
  last_active datetime not null,
  non_local boolean not null
);