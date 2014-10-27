#!/usr/bin/env python
from __future__ import with_statement   # needed for Python 2.5 only
from fabric_run_put_utils import *
from fabric.api import run, sudo, roles, env, local, put
from fabric.operations import prompt
import getpass
from fabric.contrib import files
import getpass
import os
import time

env.roledefs = {'web': ['localhost']}

def install_webstack():
    """basic server setup, starting with ISP default and ending with Apache
    set up for hosting, but with no sites"""
    
    """IMPORTANT: It is not currently possible to install MySQL unattended on Ubuntu and know the root password.
    Before running this method manually install mysql:
    > sudo apt-get -y install mysql
    > mysql -u root -p
    > create database lockify;
    > GRANT ALL PRIVILEGES ON lockify.* TO lockify_user@localhost identified by 'PASSWORD HERE'; 
    # import mysqldump file
    > mysql -u root -p lockify < dumpfile.sql
    """
    
    # Enable Apache worker MPM in /etc/sysconfig/httpd (uncomment line)
    
    # 
    #sudo ("sed 's|SELINUX=enforcing|SELINUX=permissive|' /etc/sysconfig/selinux", pty=True)
    
    # Re-sync the package indexes from their sources.
    sudo('apt-get -y update')
    
    sudo('apt-get -y install --upgrade subversion')
    
    script = """
    sudo /sbin/chkconfig autofs off
    sudo /sbin/chkconfig cups off
    sudo /sbin/chkconfig gpm off
    sudo /sbin/chkconfig hidd off
    sudo /sbin/chkconfig isdn off
    sudo /sbin/chkconfig kudzu off
    sudo /sbin/chkconfig mdmonitor off
    sudo /sbin/chkconfig xfs off
    # Disable unneeded services.
    # This has not yet been tested with an actual deploy.
    # Should restart server after making these changes.
    """
    #_run_multiline_script(script)
    
    script = """
    #sudo [ ! -d /etc/apache2 ] || service apache2 stop
    #sudo [ ! -d /etc/mysql ] || service mysql stop
    

    #sudo apt-get -y subversion
    #sudo apt-get -y groupinstall "Development Tools"
        # Development Tools will be needed to compile MySQL-python
      
    # Install the EPEL repository (already done on FireHost, but not on RedPlaid)
    # Currently, this just gives us access to a precompiled mod_wsgi.
    #sudo rpm -V epel-release-5-3 || rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-3.noarch.rpm
    
    sudo apt-get -y install --upgrade apache2
    sudo apt-get -y install libapache2-mod-wsgi
    
    # Link to the other directory where PIDs are kept
    [ ! -d /etc/apache2/rund ] || ln -s /var/run/apache2 /etc/apache2/run
    """
    _run_multiline_script(script)
    
    if env.get('CUSTOM_MYSQL'):
        # Install MySQL 5.1 for FireHost's benefit. FireHost has a newer
        # release than the standard one for CentOS/Red Hat, so we need
        # the full package in order to be able to build items dependent on
        # MySQL -- the yum repository won't have a compatible versions.
        script = """
    # Install newer version of MySQL 5.1 server & client from mysql.com--
    # not part of a trusted yum repository--to match the hosting provider's
    # recommended setup. Otherwise we'd just get version 5.0.x via
    #   yum install mysql-server.x86_64 mysql.x86_64 mysql-devel.x86_64
    # URL is redirect target of http://dev.mysql.com/get/Downloads/MySQL-5.1/MySQL-server-community-5.1.38-0.rhel5.x86_64.rpm/from/http://mysql.mirrors.pair.com/
    sudo rpm -V MySQL-server-community-5.1.42 || rpm -i http://mysql.llarian.net/Downloads/MySQL-5.1/MySQL-server-community-5.1.42-0.rhel5.x86_64.rpm
    # URL is redirect target of http://dev.mysql.com/get/Downloads/MySQL-5.1/MySQL-client-community-5.1.38-0.rhel5.x86_64.rpm/from/http://mysql.mirrors.pair.com/
    sudo rpm -V MySQL-client-community-5.1.42 || rpm -i http://mysql.llarian.net/Downloads/MySQL-5.1/MySQL-client-community-5.1.42-0.rhel5.x86_64.rpm
    # URL is redirect target of http://dev.mysql.com/get/Downloads/MySQL-5.1/MySQL-devel-community-5.1.38-0.rhel5.x86_64.rpm/from/http://mysql.mirrors.pair.com/
    sudo rpm -V MySQL-devel-community-5.1.42 || rpm -i http://mysql.llarian.net/Downloads/MySQL-5.1/MySQL-devel-community-5.1.42-0.rhel5.x86_64.rpm
        """
    else:
        # Stalls install. Can't set root password unattended. See http://templin.unfuddle.com/a#/projects/33031/tickets/by_number/1345
        #script = "sudo apt-get -y install mysql-server"
        script = ""
    _run_multiline_script(script)
    
    # If missing, install Apache
    if not files.exists('/etc/init.d/apache2', use_sudo=True) :
        script = """
        # Install Apache
        sudo apt-get -y install apache2
        
        # Modify IP Tables
        sudo /sbin/iptables -I INPUT -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT
        sudo /sbin/iptables -I OUTPUT -p tcp --sport 80 -m state --state ESTABLISHED -j ACCEPT
        sudo /sbin/iptables -I INPUT -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT
        sudo /sbin/iptables -I OUTPUT -p tcp --sport 443 -m state --state ESTABLISHED -j ACCEPT
        sudo /etc/init.d/iptables save
        
        sudo a2enmod ssl
        sudo a2ensite default-ssl
        # still need openssl?
        """
        _run_multiline_script(script)
    
    script = """
    # set up Apache modules
    sudo mkdir -p /etc/apache2/conf.d/disabled
    sudo [ ! -f /etc/apache2/conf.d/php.conf ] || mv /etc/apache2/conf.d/php.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/proxy_ajp.conf ] || mv /etc/apache2/conf.d/proxy_ajp.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/ssl.conf ] || mv /etc/apache2/conf.d/ssl.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/webalizer.conf ] || mv /etc/apache2/conf.d/webalizer.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/welcome.conf ] || mv /etc/apache2/conf.d/welcome.conf /etc/apache2/conf.d/disabled/

    # Next 4 lines remove unwanted manual.conf, perl.conf, python.conf, and
    # squid.conf if present. They were apparently present by default on
    # FireHost but not on RedPlaid.
    sudo [ ! -f /etc/apache2/conf.d/manual.conf ] || mv /etc/apache2/conf.d/manual.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/perl.conf ] || mv /etc/apache2/conf.d/perl.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/python.conf ] || mv /etc/apache2/conf.d/python.conf /etc/apache2/conf.d/disabled/
    sudo [ ! -f /etc/apache2/conf.d/squid.conf ] || mv /etc/apache2/conf.d/squid.conf /etc/apache2/conf.d/disabled/
    
    sudo [ -f /etc/apache2/conf.d/wsgi.conf ] || echo "LoadModule wsgi_module modules/mod_wsgi.so" > /etc/apache2/conf.d/wsgi.conf
    
    #sudo [ -f /etc/apache2/conf/apache2.conf.default ] || cp -p /etc/apache2/conf/apache2.conf /etc/apache2/conf/apache2.conf.default
    # enable the Apache worker MPM in /etc/sysconfig/httpd by uncommenting
    # an existing config line
    sudo sed 's|^#HTTPD=/usr/sbin/httpd\.worker$|HTTPD=/usr/sbin/httpd.worker|' /etc/sysconfig/httpd
    """
    #_run_multiline_script(script)
    
    script = """
    # install global Python packages mod_wsgi and MySQL-python
    sudo apt-get -y install libapache2-mod-wsgi python-setuptools python-dev
    sudo apt-get install -y python-pip
    sudo pip install virtualenv
    # install requirements for PIL (for creating sprites images)
    # PIL itself will be installed through requirements.txt during deploy
    sudo apt-get -y install zlib1g-dev
    """
    _run_multiline_script(script)
    
    if env.get('SPECIAL_MYSQL'):
        script = """
    # don't install MySQL-python.x86_64 via yum; it only works with the yum-installed MySQL, not the newer version from mysql.com
    sudo pip install MySQL-python
    # use pip for MySQL-python instead of of easy_install, because
    # "sudo easy_install -U MySQL-python --always-unzip" hangs (on or near
    # the package download phase).
    
    # Avert an error where MySQL-python wouldn't be able to find the shared
    # MySQL client library. Add library's parent dir to the library search path
    # (by adding a /etc/ld.so.conf.d/mysql.conf file). The LD_LIBRARY_PATH
    # env. var. would have the same effect, but it's harder to set
    # automatically in all contexts.
    # Without the change, importing MySQLdb would generate an error like this:
    # ImportError: libmysqlclient_r.so.16: cannot open shared object file: No such file or directory
    sudo [ -f /etc/ld.so.conf.d/mysql.conf ] || echo "/usr/lib64/mysql" > /etc/ld.so.conf.d/mysql.conf
    sudo /sbin/ldconfig # rebuild ld linker cache after above change
        """
    else:
        script = """
    # PROBLEM: Unlike on CentOS, this mysql install creates a  
    #sudo apt-get -y -q install python-mysqldb
    """
    _run_multiline_script(script)
    
    script = """
    # set up an Apache sites dir structure
    sudo mkdir -p /etc/apache2/sites-available
    sudo mkdir -p /etc/apache2/sites-enabled
    sudo mkdir -p /etc/apache2/ssl
    sudo chmod 700 /etc/apache2/ssl
    """
    _run_multiline_script(script)
    
    # upload custom Apache conf
    current_dir = os.path.dirname(__file__)
    put(os.path.join(current_dir, 'custom_httpd_ubuntu.conf'), '~/temp_apache2.conf') # will go to '/etc/apache2/apache2.conf'
    
    script = """
    sudo mv ~/temp_apache2.conf /etc/apache2/apache2.conf
    sudo chown root:root /etc/apache2/apache2.conf
    
    sudo update-rc.d apache2 defaults
    # above line is probably redundant on this host
    sudo update-rc.d mysql defaults
        
    sudo service apache2 start
    #sudo service mysql start
    """
    _run_multiline_script(script)
    from getpass import getpass
    mysql_root_password = getpass('Enter new MySQL root password (blank to leave alone): ')
    if mysql_root_password:
        _run_script("""
#!/bin/bash
/usr/bin/mysqladmin -u root password "%s"
""" % mysql_root_password)

def _run_multiline_script(source):
    for line in source.split("\n"):
        line = line.strip()
        if line.startswith('sudo '):
            sudo(line[5:], pty=True)
        elif line and not line.startswith('#'):
            run(line)


def _get_db_params():
    params = {}
    params['dbname'] = raw_input('Please enter the database name (blank to skip): ')
    if not params['dbname']:
        return False
    params['dbuid'] = raw_input('Please enter the new database userid: ')
    params['dbpw'] = getpass.getpass('Please enter the new MySQL database password: ')
    return params

def _setup_db_server(params):
    if not params:
        return False
    params['dbadminuid'] = 'root'
    params['dbadminpw'] = getpass.getpass('Please enter the MySQL root user\'s password: ')
    commands = """
create database %(dbname)s character set 'utf8';
grant all privileges on %(dbname)s.* to %(dbuid)s@localhost identified by '%(dbpw)s';
""" % params
    run_script(commands, 'mysql -u %(dbadminuid)s -p' % params,
        prompt='Enter password: ', password=params['dbadminpw'], pty=True)

def _upload_db_script(params):
    put(env.db_script, '%(site_home)s/db_script.sql' % env)
    script = 'mysql -u %(dbadminuid)s -p' % params + ' ieeetagsnewdev < %(site_home)s/db_script.sql' % env
    run_script(script, None,
        prompt='Enter password: ', password=params['dbadminpw'], pty=True)

def setup_db_server():
    _expand_site_paths(env)
    params = _get_db_params()
    _setup_db_server(params)
    _upload_db_script(params)

def create_blank_domain():
    _expand_site_paths(env)
    config = {'site_home': env.site_home, 'project_checkout_path': env.site_code,
        'domain': env.domain, 'short_name': env.domain.replace('.', '')}
    
    current_dir = os.path.dirname(__file__)
    
    # Populate and upload the apache config file for situations when the site is down (maintenance, etc.)
    # site_conf = open(os.path.join(current_dir, 'site.down.template.conf'), 'rU').read()
    # for var_name, value in config.iteritems():
    #     site_conf = site_conf.replace('#{%s}' % var_name, value)
    # sudo_put_data(site_conf, '/etc/apache2/sites-available/%s.down.conf'
    #     % env.domain, uid='root', gid='sudo', mode=0644)
    
    # Populate and upload the apache config file for normal operations
    site_conf = open(os.path.join(current_dir, 'site.template.conf'), 'rU').read()
    for var_name, value in config.iteritems():
        site_conf = site_conf.replace('#{%s}' % var_name, value)
    sudo_put_data(site_conf, '/etc/apache2/sites-available/%s.conf'
        % env.domain, uid='root', gid='sudo', mode=0644)
    sudo('[ -f /etc/apache2/sites-enabled/%(domain)s.conf ] || ln -s /etc/apache2/sites-available/%(domain)s.conf /etc/apache2/sites-enabled/' % env, pty=True)
    run('mkdir -p "%(site_home)s/html" "%(site_home)s/log" "%(site_home)s/python/releases"' % env)
    run('cd "%(site_home)s" && virtualenv --python=python2.6 python' % env)
    
    run('chmod o+x ~')  # Set up directory traversal permissions for the home directory, so Apache can reach ~/sites
    
    script = """
    sudo pip install -E "%(site_home)s/python" "Django==1.3.1"
    sudo pip install -E "%(site_home)s/python" "MySQL-python>=1.2.3c1"
    sudo pip install -E "%(site_home)s/python" "SPARQLWrapper>=1.4.2"
    sudo pip install -E "%(site_home)s/python" "south"
    sudo pip install -E "%(site_home)s/python" "enum"
    sudo pip install -E "%(site_home)s/python" "simplejson"
    sudo pip install -E "%(site_home)s/python" "docutils>=0.5"
    sudo pip install -E "%(site_home)s/python" "hashlib==20081119"
    sudo pip install -E "%(site_home)s/python" "django-registration==0.7"
    sudo pip install -E "%(site_home)s/python" "django-profiles==0.2"
    sudo pip install -E "%(site_home)s/python" "wsgiref"
    sudo pip install -E "%(site_home)s/python" "BeautifulSoup"
    """ % env
    run_multiline_script(script)
    
    http_username = raw_input('Enter new site basic auth username (blank to skip): ')
    if http_username:
        http_password = getpass.getpass('Enter new site basic auth password: ')
        run('/usr/bin/htpasswd -bc "%s/htpasswd" "%s" "%s"' % (env.site_home,
            http_username, http_password))
            
    # add robots.txt
    robots = """
# Disallow all
User-agent: *
Disallow: /
"""
    sudo_put_data(robots, '%s/html/robots.txt' % env.site_home)
    sudo('chown systemicist:systemicist %(site_home)s/html/robots.txt && chmod 664 %(site_home)s/html/robots.txt' % env, pty=True)
        
def checkout_site(): 
    _expand_site_paths(env)
    
    _expand_site_paths(env)
    env.release = time.strftime('%Y%m%d%H%M%S')
    code_symlink = env.site_code
    env.site_code = '%(site_home)s/python/releases/%(release)s/project' % env
    # For the remainder of the command (until cleanup at the end),
    # env.site_code points to a specific releases/xxxxx subdirectory,
    # instead of to the releases/current symlink it usually points to.
    # This is so we can set up the new release without making it current
    # until it's fully ready.
    # Be careful of calling other Fabric commands that may end up overwriting
    # env.site_code.
    
    # run_prompted('svn co'
    #     ' %(scm_url)s'
    #     ' "%(site_code)s" --no-auth-cache'
    #     ' --username=%(scm_username)s' % env,
    #     prompt="Password for '[^']+': ", password=env.scm_password, pty=True)

    params = dict(env, site_code=env.site_code)
    
    run('mkdir -p "%(site_code)s"' % env, pty=True)
    run_prompted(
        'curl %(scm_url)s/archive/%(scm_branch)s.zip -o %(site_code)s/../%(scm_branch)s.zip --user %(scm_username)s -L --verbose -k' % params,
        prompt="Enter host password for user '%(scm_username)s':" % params,
        password=env.scm_password, pty=True)
    run('unzip -q  %(site_code)s/../%(scm_branch)s.zip -d %(site_code)s/../' % params)
    #run('rm -r %(site_code)s/../project' % params)
    run('mv -T %(site_code)s/../ieeetags-%(scm_branch)s %(site_code)s/../project' % params)
    

    # Make a 'ieeetags' link to the 'project' directory. References to the ieeetags module are hardcoded in codebase.
    # run('ln -s %(site_code)s %(site_code)s/../ieeetags' % env)

    if files.exists("%s/ieeetags/local_settings.py" % code_symlink):
        run('cp -p "%s/ieeetags/local_settings.py" "%s/ieeetags/"' % (code_symlink, env.site_code))
    
    # Install package requirements
    # run('cd "%(site_home)s/python" && source bin/activate && cd "%(site_home)s/python/releases/current/project/" && pip install -r requirements.txt' % env)

    # Create log.txt
    run('touch %(site_code)s/log.txt' % env)
    run('chmod 666 %(site_code)s/log.txt' % env)
        
    sudo('mkdir -p "%(site_code)s/ieeetags/media/caches"' % env, pty=True)
    sudo('chmod 777 "%(site_code)s/ieeetags/media/caches"' % env, pty=True)
    sudo('chmod o+x ~', pty=True)
    
    # Move the site_down directory to /html/maintenance. When the instance.lockify.com.down.conf config file is used
    # all request will serve the default file in this directory.    
    run('rm -rf %(site_home)s/html/maintenance' % env)
    run('mv %(site_code)s/site_down %(site_home)s/html/maintenance' % env)
    
    #run('cd "%(site_home)s/python" && source bin/activate && [ ! -d "%(site_code)s/migrations" ] || python "%(site_code)s/manage.py" migrate ieeetags' % env)
    
    # Redirect the 'current' and 'previous' symlinks.
    run('cd "%(site_home)s/python/releases" && ( [ ! -d previous ] || rm previous ) && ( [ ! -d current ] || mv current previous )' % env)
    run('cd "%(site_home)s/python/releases" && ln -s %(release)s current' % env)
    # Use sudo for next line. Some cached django media files won't delete otherwise.
    sudo('cd "%(site_home)s/python/releases" && rm -rf $(ls | grep -v -E previous\|current\|`readlink previous`\|`readlink current`)' % env, pty=True)
    
    # Old apply syncdb and south migrations
    # run('cd "%(site_home)s/python" && source bin/activate && cd "%(site_home)s/python/releases/current/project/" && export PYTHONPATH=..:../../../lib/python2.6/site-packages/ && python "%(site_code)s/manage.py" syncdb --noinput && python manage.py migrate --fake ' % env)

    # Apply collectstatic.
    run('cd "%(site_home)s/python" && source bin/activate && cd "%(site_home)s/python/releases/current/project/" && export PYTHONPATH=..:../../../lib/python2.6/site-packages/ && python "%(site_code)s/manage.py" collectstatic' % env)

    # Apply migrations.
    run('cd "%(site_home)s/python" && source bin/activate && cd "%(site_home)s/python/releases/current/project/" && export PYTHONPATH=..:../../../lib/python2.6/site-packages/ && python "%(site_code)s/manage.py" migrate --noinput' % env)

    env.site_code = code_symlink
    run('touch "%(site_code)s/start-wsgi.py"' % env)
    
    #sudo('/etc/init.d/apache2 restart', pty=True)

def build_tagcloud_caches():
    _expand_site_paths(env)
    run('cd "%(site_home)s/python" && source bin/activate && export PYTHONPATH=%(site_code)s/..:%(site_code)s/:$PYTHONPATH && export DJANGO_SETTINGS_MODULE=ieeetags.settings &&  python %(site_code)s/deploy/create_caches.py' % env)
    #run('python deploy/create_caches.py create_caches')
    
def install_siteminder_client():
    script = """
    # Install required packages
    sudo apt-get -y install compat-gcc-34
    sudo apt-get -y install compat-libstdc++-33
    sudo apt-get -y install compat-gcc-34-c++
    """
    run_multiline_script(script)
    
    # Upload the siteminder installer and properties files.
    put(env.siteminder_properties_file, '~/', mode=0644)
    put(env.siteminder_installer_file, '~/', mode=0644)
    
    # Unzip and run the siteminder installer file.
    script="""
    sudo apt-get -y install zip unzip
    unzip %s
    sudo chmod +x nete-wa-6qmr5-cr027-rhas30-x86-64.bin
    sudo ./nete-wa-6qmr5-cr027-rhas30-x86-64.bin -f %s -i silent
    rm -f nete-wa-6qmr5-cr027-rhas30-x86-64.bin readme.txt
    """ % (os.path.split(env.siteminder_installer_file)[1], env.siteminder_properties_file)
    run_multiline_script(script)

def _expand_site_paths(env):
    """
    Call this at the beginning of a Fabric command to expand several
    user-relative paths in env, so that they can be included in double-quotes.
    See set_ieee_domain.
    """
    for name in ('site_home', 'site_python_root', 'site_code'):
        if 'abbr_' + name in env:
            env[name] = _expand_site_path(env['abbr_' + name])

def _expand_site_path(path):
    if path[:1] == '~':
        path = '/home/%s%s' % (env.user, path[1:])
    return path

def set_ieee_domain(domain, subdomain):
    """
    Internal function.
    
    Set up vars in env to point to paths relevant to the given main domain
    and subdomain.
    
    This is usually called one time by other commands during initialization.
    We can't rely on env.user being set (it may be set to multiple different
    usernames as commands run on different servers) so use '~' to represent
    the user's home directory for now. Many commands will require an exact
    path, so the caller should call '_expand_site_paths(env)' while running
    particular command instance to fix up the paths and store them without
    an 'abbr_' prefix in env.
    
    """
    
    env.domain = domain
    env.subdomain = subdomain
    
    env.abbr_site_home = '~/sites/%s' % env.domain
    env.abbr_site_python_root = env.abbr_site_home + '/python'
    env.abbr_site_code = env.abbr_site_python_root + '/releases/current/project'
    env.make_checksum_args = ''
    
def status():
    'Returns "enabled", "disabled"'
    site_status = sudo(' if [ -f /etc/apache2/sites-enabled/%(domain)s.conf ]; then echo enabled; elif [ -f /etc/apache2/sites-enabled/%(domain)s.down.conf ]; then echo disabled; fi' % env, pty=True)
    return site_status
    
def disable():
    'Puts the site into "maintenance" mode.'
    site_status = status()
    if site_status == 'disabled':
        print 'Site is already disabled. Doing nothing.'
        return
    if site_status == 'enabled':
        sudo(' if [ -f /etc/apache2/sites-enabled/%(domain)s.conf ]; then unlink /etc/apache2/sites-enabled/%(domain)s.conf; fi' % env, pty=True)
        
    sudo ('ln -s /etc/apache2/sites-available/%(domain)s.down.conf /etc/apache2/sites-enabled/ && /sbin/service apache2 restart' % env, pty=True)
    print 'Site successfully disabled.'

def enable():
    'Take the site out of "maintenance" mode.'
    site_status = status()
    if site_status == 'enabled':
        print 'Site is already enabled. Doing nothing.'
        return
    if site_status == 'disabled':
        sudo(' if [ -f /etc/apache2/sites-enabled/%(domain)s.down.conf ]; then unlink /etc/apache2/sites-enabled/%(domain)s.down.conf; fi' % env, pty=True)
        
    sudo(' ln -s /etc/apache2/sites-available/%(domain)s.conf /etc/apache2/sites-enabled/ && /sbin/service apache2 restart' % env, pty=True)    
    print 'Site successfully enabled.'

