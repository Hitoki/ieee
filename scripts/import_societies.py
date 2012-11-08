from sys import argv
import csv
import MySQLdb

script, filepath, society_name = argv

host = ''
user = ''
pw = ''
db = ''

mydb = MySQLdb.connect (host = host,
                 user = user,
                 passwd = pw,
                 db = db)

cursor = mydb.cursor()
reader = csv.reader(open(filepath, "rb"))

cursor.execute('INSERT INTO ieeetags_society(name) VALUES(%s)', society_name)

society_id = cursor.lastrowid

for row in reader:
	if row[2] == '1':
		cursor.execute('INSERT INTO ieeetags_node_societies(node_id, society_id) VALUES(%s, %s)', 
	    (row[0], society_id))

mydb.commit()
cursor.close()    
