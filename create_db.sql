SET NAMES utf8;
-- Recreate the DB, create user, grant all DB privileges to user
DROP DATABASE IF EXISTS ieeetags;
--CREATE DATABASE ieeetags;
CREATE DATABASE ieeetags CHARACTER SET utf8 COLLATE utf8_unicode_ci;
-- Ignore ERROR for create user commmand, user may already exist
CREATE USER ieeetags@localhost IDENTIFIED BY 'ieeetags';
GRANT ALL ON ieeetags.* TO ieeetags@localhost;
