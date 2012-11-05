import csv
import MySQLdb

host = ''
user = ''
pw = ''
db = ''

mydb = MySQLdb.connect (host = host,
                 user = user,
                 passwd = pw,
                 db = db)

cursor = mydb.cursor()
filepath = '/home/ubuntu/Downloads/IEEE Initiative Clusters 10-18-2012 - TE.csv'
reader = csv.reader(open(filepath, "rb"))

society_name = ''

cursor.execute('INSERT INTO ieeetags_society(name)' \
	          'VALUES("%s")', society_name)

society_id = ''

for row in reader:
	if row[2] == 1:
		cursor.execute('INSERT INTO ieeetags_node_society(node_id, \
	          society_id)' \
	          'VALUES("%s", "%s")', 
	    row[0], society_id)

mydb.commit()
cursor.close()    