import subprocess
import settings

def run_mysql_cmd(cmd):
    args = [
        'mysql',
        '--user=%s' % settings.DATABASE_USER,
        '--password=%s' % settings.DATABASE_PASSWORD,
        '%s' % settings.DATABASE_NAME,
        '-e',
        cmd,
    ]
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    result = process.communicate()[0]
    #print 'stderr:', process.communicate()[1]
    return result
    
def main():
    MAX_ITERATIONS = 15
    
    count = 0
    table_names = [1]
    
    # Loop through and keep dropping tables until there are none left (due to foreign key constraints, some tables wont drop the first time around)
    while len(table_names) > 0 and count < MAX_ITERATIONS:
        cmd = 'SHOW TABLES;'
        result = run_mysql_cmd(cmd)
        table_names = result.strip().split('\r\n')
        del table_names[0]

        drop_cmd = ''
        print 'There are %d tables' % len(table_names)
        for table_name in table_names:
            print 'Dropping table %s' % table_name
            drop_cmd = 'DROP TABLE %s;\r\n' % table_name
            run_mysql_cmd(drop_cmd)
        
        count += 1

    cmd = 'SHOW TABLES;'
    result = run_mysql_cmd(cmd).strip()
    
    if result != '':
        print 'Tables remaining:'
        print result
    

if __name__ == '__main__':
    main()
    