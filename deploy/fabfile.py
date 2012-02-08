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
    script = """
    
    # Install Apache
    sudo yum -y install httpd
    
    # Modify IP Tables
    sudo /sbin/iptables -I INPUT -p tcp --dport 80 -m state --state NEW,ESTABLISHED -j ACCEPT
    sudo /sbin/iptables -I OUTPUT -p tcp --sport 80 -m state --state ESTABLISHED -j ACCEPT
    sudo /sbin/iptables -I INPUT -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT
    sudo /sbin/iptables -I OUTPUT -p tcp --sport 443 -m state --state ESTABLISHED -j ACCEPT
    sudo /etc/init.d/iptables save
    
    sudo yum -y install mod_ssl
    sudo yum -y install subversion
    
    sudo /etc/init.d/httpd stop
    
    # Install the EPEL repository
    # Currently, this just gives us access to a precompiled mod_wsgi.
    sudo rpm -V epel-release-5-3 || rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-3.noarch.rpm
    """
    run_multiline_script(script)
    
    script = """
    # set up Apache modules
    sudo mkdir -p /etc/httpd/conf.d/disabled
    sudo [ ! -f /etc/httpd/conf.d/php.conf ] || mv /etc/httpd/conf.d/php.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/proxy_ajp.conf ] || mv /etc/httpd/conf.d/proxy_ajp.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/ssl.conf ] || mv /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/webalizer.conf ] || mv /etc/httpd/conf.d/webalizer.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/welcome.conf ] || mv /etc/httpd/conf.d/welcome.conf /etc/httpd/conf.d/disabled/
    
    # Next 4 lines remove unwanted manual.conf, perl.conf, python.conf, and
    # squid.conf if present.
    sudo [ ! -f /etc/httpd/conf.d/manual.conf ] || mv /etc/httpd/conf.d/manual.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/perl.conf ] || mv /etc/httpd/conf.d/perl.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/python.conf ] || mv /etc/httpd/conf.d/python.conf /etc/httpd/conf.d/disabled/
    sudo [ ! -f /etc/httpd/conf.d/squid.conf ] || mv /etc/httpd/conf.d/squid.conf /etc/httpd/conf.d/disabled/
    
    sudo [ -f /etc/httpd/conf/httpd.conf.default ] || cp -p /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.default
    # enable the Apache worker MPM in /etc/sysconfig/httpd by uncommenting
    # an existing config line
    sudo sed 's|^#HTTPD=/usr/sbin/httpd\.worker$|HTTPD=/usr/sbin/httpd.worker|' /etc/sysconfig/httpd    
    """
    run_multiline_script(script)
    
    script = """
    # enable the Apache worker MPM in /etc/sysconfig/httpd by uncommenting
    # an existing config line
    sudo sed 's|^#HTTPD=/usr/sbin/httpd\.worker$|HTTPD=/usr/sbin/httpd.worker|' /etc/sysconfig/httpd
    """
    run_multiline_script(script)
    
    # Change server name
    # in /etc/httpd/conf/httpd.conf find  replace with "ServerName ieeetags"
    #files.sed('/etc/httpd/conf/httpd.conf', before='#ServerName www.example.com:80', after='ServerName ieeetags', use_sudo=True, pty=True)
    
    # install global Python packages, mod_wsgi, and virtualenv
    script = """
    sudo yum -y install mod_wsgi.x86_64 python-setuptools python-devel.x86_64
    # wget http://codepoint.net/attachments/mod_wsgi/mod_wsgi-3.1-1.el5.x86_64.rpm
    # sudo rpm -i mod_wsgi-3.1-1.el5.x86_64.rpm
    sudo rpm -V epel-release-5-3 || rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-3.noarch.rpm
    sudo [ -f /etc/httpd/conf.d/wsgi.conf ] || echo "LoadModule wsgi_module modules/mod_wsgi.so" > /etc/httpd/conf.d/wsgi.conf
    sudo easy_install -U pip
    sudo pip install virtualenv
    """
    run_multiline_script(script)
    
    script = """
    # install PIL and its requirements (for creating sprites images)
    sudo yum -y install zlib-devel
    sudo yum -y install gcc
    sudo pip install pil
    """
    run_multiline_script(script)
    
    # Install MySQL
    sudo ('yum -y install mysql-server.x86_64 mysql.x86_64 mysql-devel.x86_64', pty=True)
    
    # Install MySQL-Python
    script = "sudo yum -y install MySQL-python.x86_64"
    run_multiline_script(script)
    
    # Install Django
    script = """
    wget http://www.djangoproject.com/download/1.1.1/tarball/
    tar xzvf Django-1.1.1.tar.gz
    sudo python Django-1.1.1/setup.py build
    sudo python Django-1.1.1/setup.py install
    """
    run_multiline_script(script)
    
    script = """
    # set up an Apache sites dir structure
    sudo mkdir -p /etc/httpd/sites-available
    sudo mkdir -p /etc/httpd/sites-enabled
    sudo mkdir -p /etc/httpd/ssl
    sudo chmod 700 /etc/httpd/ssl
    """
    run_multiline_script(script)
    
    # upload custom Apache conf
    current_dir = os.path.dirname(__file__)
    put(os.path.join(current_dir, 'custom_httpd.conf'), '~/temp_httpd.conf') # will go to '/etc/httpd/conf/httpd.conf'
    
    script = """
    sudo mv ~/temp_httpd.conf /etc/httpd/conf/httpd.conf
    sudo chown root:root /etc/httpd/conf/httpd.conf
    """
    run_multiline_script(script)
    
    # Set services to auto-restart if slice is rebooted. Might be redundant.
    # Restart Services
    script = """
    sudo /sbin/chkconfig httpd on
    sudo /sbin/chkconfig mysqld on	
    sudo /etc/init.d/httpd restart
    sudo /etc/init.d/mysqld start
    """
    run_multiline_script(script)
    
    mysql_root_password = getpass.getpass('Enter new MySQL root password (blank to leave alone): ')
    if mysql_root_password:
        #run('/usr/bin/mysqladmin -u root password "%s"' % mysql_root_password)
        run_script("""
#!/bin/bash
/usr/bin/mysqladmin -u root password "%s"
""" % mysql_root_password)

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
    # sudo_put_data(site_conf, '/etc/httpd/sites-available/%s.down.conf'
    #     % env.domain, uid='root', gid='wheel', mode=0644)
    
    # Populate and upload the apache config file for normal operations
    site_conf = open(os.path.join(current_dir, 'site.template.conf'), 'rU').read()
    for var_name, value in config.iteritems():
        site_conf = site_conf.replace('#{%s}' % var_name, value)
    sudo_put_data(site_conf, '/etc/httpd/sites-available/%s.conf'
        % env.domain, uid='root', gid='wheel', mode=0644)
    sudo('[ -f /etc/httpd/sites-enabled/%(domain)s.conf ] || ln -s /etc/httpd/sites-available/%(domain)s.conf /etc/httpd/sites-enabled/' % env, pty=True)
    run('mkdir -p "%(site_home)s/html" "%(site_home)s/log" "%(site_home)s/python/releases"' % env)
    run('cd "%(site_home)s" && virtualenv --python=python2.4 python' % env)
    
    run('chmod o+x ~')  # Set up directory traversal permissions for the home directory, so Apache can reach ~/sites
    
    script = """
    sudo pip install -E "%(site_home)s/python" "Django==1.2.3"
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
        
    # Set up SELinux security under RHEL/CentOS
    sudo('chcon system_u:object_r:httpd_sys_content_t "%s/html"' % env.site_home, pty=True)
    # must check out some code and restart Apache before use

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
    
    run_prompted('svn co'
        ' %(scm_url)s'
        ' "%(site_code)s" --no-auth-cache'
        ' --username=%(scm_username)s' % env,
        prompt="Password for '[^']+': ", password=env.scm_password, pty=True)
        
    # Make a 'ieeetags' link to the 'project' directory. References to the ieeetags module are hardcoded in codebase.
    run('ln -s %(site_code)s %(site_code)s/../ieeetags' % env);
    
    if files.exists("%s/local_settings.py" % code_symlink):
        run('cp -p "%s/local_settings.py" "%s/"' % (code_symlink, env.site_code))
    
    # Create log.txt
    run('touch %(site_code)s/log.txt' % env)
    run('chmod 666 %(site_code)s/log.txt' % env)
        
    sudo('mkdir -p "%(site_code)s/media/caches"' % env, pty=True)
    sudo('chmod 777 "%(site_code)s/media/caches"' % env, pty=True)
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
    
    # Apply any south migrations.
    run('cd "%(site_home)s/python" && source bin/activate && cd "%(site_home)s/python/releases/current/ieeetags/" && export PYTHONPATH=..:../../../lib/python2.6/site-packages/ && python "%(site_code)s/manage.py" syncdb --noinput && python manage.py migrate --delete-ghost-migrations' % env)
    
    env.site_code = code_symlink
    run('touch "%(site_code)s/start-wsgi.py"' % env)
    
    #sudo('/etc/init.d/httpd restart', pty=True)

def build_tagcloud_caches():
    _expand_site_paths(env)
    run('cd "%(site_home)s/python" && source bin/activate && export PYTHONPATH=%(site_code)s/..:%(site_code)s/:$PYTHONPATH && export DJANGO_SETTINGS_MODULE=ieeetags.settings &&  python %(site_code)s/deploy/create_caches.py' % env)
    #run('python deploy/create_caches.py create_caches')
    
def install_siteminder_client():
    script = """
    # Install required packages
    sudo yum -y install compat-gcc-34
    sudo yum -y install compat-libstdc++-33
    sudo yum -y install compat-gcc-34-c++
    """
    run_multiline_script(script)
    
    # Upload the siteminder installer and properties files.
    put(env.siteminder_properties_file, '~/', mode=0644)
    put(env.siteminder_installer_file, '~/', mode=0644)
    
    # Unzip and run the siteminder installer file.
    script="""
    sudo yum -y install zip unzip
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
    site_status = sudo(' if [ -f /etc/httpd/sites-enabled/%(domain)s.conf ]; then echo enabled; elif [ -f /etc/httpd/sites-enabled/%(domain)s.down.conf ]; then echo disabled; fi' % env, pty=True)
    return site_status
    
def disable():
    'Puts the site into "maintenance" mode.'
    site_status = status()
    if site_status == 'disabled':
        print 'Site is already disabled. Doing nothing.'
        return
    if site_status == 'enabled':
        sudo(' if [ -f /etc/httpd/sites-enabled/%(domain)s.conf ]; then unlink /etc/httpd/sites-enabled/%(domain)s.conf; fi' % env, pty=True)
        
    sudo ('ln -s /etc/httpd/sites-available/%(domain)s.down.conf /etc/httpd/sites-enabled/ && /sbin/service httpd restart' % env, pty=True)
    print 'Site successfully disabled.'

def enable():
    'Take the site out of "maintenance" mode.'
    site_status = status()
    if site_status == 'enabled':
        print 'Site is already enabled. Doing nothing.'
        return
    if site_status == 'disabled':
        sudo(' if [ -f /etc/httpd/sites-enabled/%(domain)s.down.conf ]; then unlink /etc/httpd/sites-enabled/%(domain)s.down.conf; fi' % env, pty=True)
        
    sudo(' ln -s /etc/httpd/sites-available/%(domain)s.conf /etc/httpd/sites-enabled/ && /sbin/service httpd restart' % env, pty=True)    
    print 'Site successfully enabled.'

