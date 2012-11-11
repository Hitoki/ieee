from sys import argv
import csv
import MySQLdb

script, filepath, society_name, society_id = argv

host = 'localhost'
user = 'root'
pw = 'root'
db = 'ieeetagsnewdev'

mydb = MySQLdb.connect (host = host,
                 user = user,
                 passwd = pw,
                 db = db)

cursor = mydb.cursor()
reader = csv.reader(open(filepath, "rb"))

if society_id == None:
        cursor.execute('INSERT INTO ieeetags_society(name) VALUES(%s)', society_name)
        society_id = cursor.lastrowid

for row in reader:
	if row[2] == '1':
		cursor.execute('INSERT INTO ieeetags_node_societies(node_id, society_id, date_created) VALUES(%s, %s, NOW())', 
	    (row[0], society_id))

mydb.commit()
cursor.close()    
