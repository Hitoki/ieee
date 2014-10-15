--ALTER TABLE ieeetags_resource DROP COLUMN priority_to_tag;
ALTER TABLE ieeetags_resource ADD COLUMN priority_to_tag TINYINT(1);
UPDATE ieeetags_resource SET priority_to_tag = false;
