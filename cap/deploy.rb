# 
# Capistrano capfile include to upgrade the Django project, apply dmigrate
# database migrations, and restart Apache.
#
# To use, make sure Capistrano is installed (gem install capistrano),
# switch to the directory containing this file, enter "cap --tasks".
#
# To use under Plesk, make sure that under Setup, only 'FastCGI' is checked.
# Python and PHP should be disabled, because we prefer mod_wsgi with daemon
# processes for Python, and mod_fcgid for PHP, to cut down on Apache child
# process size. If 'CGI' were also checked, Plesk would attempt to use Suexec
# with FastCGI, which doesn't work with this setup because all subdomains
# currently share a single PHP interpreter owned by root.
#
# To consider: Uncomment the line in /etc/sysconfig/httpd that enables the
# Apache worker MPM:
# HTTPD=/usr/sbin/httpd.worker
#
# Portions based on example Django capfile
# (c) Ville Säävuori <ville@unessa.net>, 2007
# http://www.unessa.net/en/hoyci/
# 
#
# Make a file named 'capfile' in the parent directory's 'cap' subdirectory,
# with contents like this:
# ---
# set :project_homes, ["~", "~/subdomains/mysubdomain", "~/subdomains/myothersubdomain"]
# set :scm_username, "myreadonlysvnuser"
# set :scm_password, "myreadonlysvnpass"
# role :web, "mydomainuser@mydomain.com"
# set :site_features, ['nooengine_full', 'project', 'themes', 'facebook_connect', 'openid']
# load "../../nooengine/cap/deploy.rb"
# ---
# Then, make sure Capistrano is installed (gem install capistrano),
# switch to the directory containing the capfile, and enter "cap --tasks".
#############################################################################

# Set repository based on SVN keywords.
# See http://flow.handle.it/past/2007/11/11/capistrano_and_svn_tags_branches/
set :repository, "$HeadURL: https://templin.unfuddle.com/svn/templin_nooengine/trunk/djangonaut-project/cap/deploy.rb $".split[1].
   gsub(%r{(trunk|(?:branches/|tags/)[^/]+).*},'\1')
   
namespace :deploy do
    desc "Upgrades the project on the remote server."
    task :upgrade, :roles => :web do
    
        project_homes.each do |project_path|
            
            project_checkout_path = project_path + '/python/nooengine'
            
            # getting the current revision number
            run "svn info #{project_checkout_path} | grep ^Revision" do |channel, stream, data|
                set :rev, data.split(' ')[1]
            end
    
            # updating new files
            run "svn update #{project_checkout_path} --username=#{scm_username}" do |ch, stream, out|
                ch.send_data "#{scm_password}\n" if out =~ /^Password for '[\w]+':/
                puts out
            end

            run "svn info #{project_checkout_path} | grep ^Revision" do |channel, stream, data|
                set :this_rev, data.split(' ')[1]
            end

            if rev != this_rev
                #run "sudo /etc/init.d/apache2 reload"
                puts "Upgraded #{project_checkout_path} from revision #{rev} to #{this_rev}."
            else
                puts "Did not upgrade project. Revision still at #{rev}."
            end
            run "env PYTHONPATH=`dirname #{project_checkout_path}` PYTHON_EGG_CACHE=`dirname #{project_checkout_path}`/python-egg-cache python #{project_checkout_path}/manage.py dmigrate all"
        end
        deploy.restart_site
    end

    task :restart_site, :roles => :web do
        project_homes.each do |project_path|
            run "touch #{project_path}/python/nooengine/start-wsgi.py"
        end
        puts "Restarted site."
    end

    task :restart_apache, :roles => :web do
        default_run_options[:pty] = true # or else you'll get "sorry, you must have a tty to run sudo" 
        sudo "/usr/local/psa/admin/sbin/websrvmng -a -v"
        puts "Restarted Apache."
    end

    task :downgrade, :roles => :web do
        # 501 Not Implemented
    end
    
    task :dbbackup, :roles => :web do
        project_homes.each do |project_path|
            filename = "/work/backups/#{Time.now.strftime('%Y%m%dT%H%M%S')}.sql.gz"
            run "[ -d #{project_path}/work/backups ] || mkdir #{project_path}/work/backups"
            run "cd #{project_path}/python/nooengine && python -c 'import local_settings; print \"STASH PW: \" + local_settings.DATABASE_PASSWORD' && mysqldump -u \`python -c 'import local_settings; print local_settings.DATABASE_USER'\` -p \`python -c 'import local_settings; print local_settings.DATABASE_NAME'\` | gzip > #{project_path}#{filename}" do |ch, stream, out|
                ch[:stash_pw] = out[10..-1].chomp if out =~ /^STASH PW: (.*)\n/
                #print ch[:stash_pw]
                #ch.send_data "\`cd #{project_path}/python/nooengine && python -c 'import local_settings; print local_settings.DATABASE_PASSWORD'\`\n" if out =~ /^Enter password:/
                ch.send_data "#{ch[:stash_pw]}\n" if out =~ /^Enter password:/
            end
        end
    end
    
    task :djangobackup, :roles => :web do
        # +++ should only do this for a primary app server; others will be dups
        project_homes.each do |project_path|
            timestamp = Time.now.strftime('%Y%m%dT%H%M%S')
            run "[ -d #{project_path}/work/backups ] || mkdir #{project_path}/work/backups"
            run "PYTHONPATH=#{project_path}/python PYTHON_EGG_CACHE=#{project_path}/python-egg-cache python #{project_path}/python/nooengine/manage.py dumpdata > #{project_path}/work/backups/#{timestamp}.json"
        end
    end
    
    desc "Run a Django manage.py command specified by the COMMAND variable"
    task :manage, :roles => :web do
        command = ENV["COMMAND"] || ""
        abort "Please specify a command to execute on the remote servers (via the COMMAND environment variable)" if command.empty?
        project_homes.each do |project_path|
            run " ( [ -f #{project_path}/python/project/manage.py ] && PYTHONPATH=#{project_path}/python PYTHON_EGG_CACHE=#{project_path}/python-egg-cache python #{project_path}/python/project/manage.py #{command} ) || ( [ ! -f #{project_path}/python/project/manage.py ] && PYTHONPATH=#{project_path}/python PYTHON_EGG_CACHE=#{project_path}/python-egg-cache #{project_path}/python/nooengine/manage.py #{command} )"
        end
    end
    
    desc "Set the database's character set to UTF8, how it should be"
    task :setdbcharset, :roles => :web do
        project_homes.each do |project_path|
            run "echo 'ALTER DATABASE DEFAULT CHARACTER SET utf8' | PYTHONPATH=#{project_path}/python PYTHON_EGG_CACHE=#{project_path}/python-egg-cache python #{project_path}/python/nooengine/manage.py dbshell"
        end
    end
     
    desc "Run a SQL statement specified by the COMMAND variable (avoid double quotes)"
    task :dbinvoke, :roles => :web do
        command = ENV["COMMAND"] || ""
        abort "Please specify a command to execute on the remote servers (via the COMMAND environment variable)" if command.empty?
        project_homes.each do |project_path|
            run "echo \"#{command}\" | PYTHONPATH=#{project_path}/python PYTHON_EGG_CACHE=#{project_path}/python-egg-cache python #{project_path}/python/nooengine/manage.py dbshell"
        end
    end
     
    desc "Update project name from nautsite to nooengine (one-time use)"
    task :updateprojectname, :roles => :web do
        project_homes.each do |project_path|
            run "mv #{project_path}/python/nautsite #{project_path}/python/nooengine"
        end
    end
     
    desc "Set up a site from scratch"
    task :coldsetup, :roles => :web do
        unless variables.include?(:django_only)
            set :django_only, false
        end
        unless variables.include?(:site_features)
            if :django_only
                set :site_features, ['project']
            else
                set :site_features, ['nooengine_full', 'themes', 'facebook_connect', 'openid']
            end
        end
        project_homes.each do |project_path|
            project_checkout_path = project_path + '/python/project'
                
            default_run_options[:pty] = true # or else you'll get "sorry, you must have a tty to run sudo" 
            set(:rootpw) do
                Capistrano::CLI.ui.ask("Please enter the root password: ")
            end
            run "cd #{project_path} && export SAVEDUSER=`whoami` && su root" do |ch, stream, out|
                cmds = "#{rootpw}\n" + <<-END
mkdir python work python-egg-cache
chown $SAVEDUSER:psaserv python work python-egg-cache
chmod o-rwx python work python-egg-cache
chmod g+w python-egg-cache
easy_install --upgrade --always-unzip mysql-python
exit
END
                ch.send_data cmds if out =~ /^Password/
                #ch.send_data "mkdir python work python-egg-cache\n"
                #chown #{user}:psaserv python work python-egg-cache"
                #puts ch[:user]
                #puts out
            end
            
        
            run "cd #{project_path} && ( [ ! -f httpdocs/index.html ] || mv httpdocs/index.html httpdocs/factory-index.html )"
            
            # Create project directory separate from nooengine, if requested
            if site_features.include?('project')
                run "[ -d #{project_checkout_path} ] || mkdir #{project_checkout_path}"
            end
            
            # Install nooengine, if turned on
            if site_features.include?('nooengine_full') or site_features.include?('nooengine_partial')
                nooengine_checkout_path = project_path + '/python/nooengine'
                run "cd #{project_path} && ( [ -d #{nooengine_checkout_path} ] || svn co https://templin.unfuddle.com/svn/templin_nooengine/trunk/djangonaut-project/ #{nooengine_checkout_path} --username=#{scm_username} )" do |ch, stream, out|
                    ch.send_data "#{scm_password}\n" if out =~ /^Password for '[\w]+':/
                    puts out
                end
                # make nooengine the project directory if we haven't already created a separate one
                run "[ -d #{project_checkout_path} ] || ( cd #{project_path}/python && ln -s nooengine project )"
            else
                # no nooengine; make django-only project self-sufficient
                run "[ -f #{project_checkout_path}/settings.py ] || echo \"from local_settings import *\" > #{project_checkout_path}/settings.py"
                #run "[ -f #{project_checkout_path}/start-wsgi.py ] ||"
                put File.read(File.join(File.dirname(File.dirname(__FILE__)), 'start-wsgi.py')), project_checkout_path[2..-1] + '/start-wsgi.py'
            end
            
            run "[ -d #{project_checkout_path}/media ] || mkdir #{project_checkout_path}/media"
            
            # Grant Django media cache and upload permissions for write access
            run "cd #{project_path} && export SAVEDUSER=`whoami` && su root" do |ch, stream, out|
                cmds = "#{rootpw}\n" + <<-END
[ -d python/project/media/caches ] || mkdir python/project/media/caches
[ -d python/project/media/caches/css ] || mkdir python/project/media/caches/css
[ -d python/project/media/caches/js ] || mkdir python/project/media/caches/js
[ -d python/project/media/caches/imagesize ] || mkdir python/project/media/caches/imagesize
[ -d python/project/media/user-image ] || mkdir python/project/media/user-image
chown -R $SAVEDUSER:psaserv python/project/media/caches
chmod -R 760 python/project/media/caches
chown -R $SAVEDUSER:psaserv python/project/media/user-image
chmod -R 760 python/project/media/user-image
END
                if site_features.include?('nooengine_full') or site_features.include?('nooengine_partial')
                    # Temp: repeat the same operation in NooEngine, so the
                    # permissions will be correct whether we're serving out
                    # of the project directory or out of NooEngine. No harm
                    # done if they're one and the same.
                    cmds += <<-END
[ -d python/nooengine/media/caches ] || mkdir python/nooengine/media/caches
[ -d python/nooengine/media/caches/css ] || mkdir python/nooengine/media/caches/css
[ -d python/nooengine/media/caches/js ] || mkdir python/nooengine/media/caches/js
[ -d python/nooengine/media/caches/imagesize ] || mkdir python/nooengine/media/caches/imagesize
[ -d python/nooengine/media/user-image ] || mkdir python/nooengine/media/user-image
chown -R $SAVEDUSER:psaserv python/nooengine/media/caches
chmod -R 770 python/nooengine/media/caches
chown -R $SAVEDUSER:psaserv python/nooengine/media/user-image
chmod -R 770 python/nooengine/media/user-image
END
                end
                
                cmds += "exit\n"
                ch.send_data cmds if out =~ /^Password/
            end

            
            #run "cd #{project_path} && ( [ -d python/nooengine/media/caches ] || mkdir python/nooengine/media/caches ) && chmod -R go+w python/nooengine/media/caches"
            ##run "cd #{project_path} && ( [ -d python/nooengine/media/caches/css ] || mkdir python/nooengine/media/caches/css ) && chmod +w python/nooengine/media/caches/css"
            ##run "cd #{project_path} && ( [ -d python/nooengine/media/imagecache ] || mkdir python/nooengine/media/imagecache ) && chmod +w python/nooengine/media/imagecache"
            run "cd #{project_path} && ( [ -d python/django-1.0 ] || svn co http://code.djangoproject.com/svn/django/branches/releases/1.0.X/ python/django-1.0 )"
            run "cd #{project_path} && ( ln -fs django-1.0/django python/django )"
            run "cd #{project_path} && ( [ -d python/dmigrations ] || svn co http://dmigrations.googlecode.com/svn/trunk/dmigrations python/dmigrations )"
            run "cd #{project_path} && ( [ -d python/registration ] || svn co http://django-registration.googlecode.com/svn/trunk/registration/ python/registration )"
            
            if site_features.include?('openid')
            
                # Add hashlib, a prerequisite for the Python openid package under
                # Python 2.4. (It's already bundled with Python 2.5.)
                # This is done globally as root.
                run "cd #{project_path} && su root" do |ch, stream, out|
                    cmds = "#{rootpw}\neasy_install hashlib\nexit\n"
                    ch.send_data cmds if out =~ /^Password/
                end
            
                # Add Python openid package, a prerequisite for django_openid app.
                run "cd #{project_path} && ( [ -d python/temp-openid ] || mkdir python/temp-openid )"
                run "cd #{project_path}/python/temp-openid && ( [ -d ../openid ] || ( wget http://openidenabled.com/files/python-openid/packages/python-openid-2.2.1.tar.gz && tar xvf python-openid-2.2.1.tar.gz && cd python-openid-2.2.1 && python setup.py install --install-purelib=#{project_path}/python --install-scripts=#{project_path}/python ) )"
                run "rm -rf #{project_path}/python/temp-openid"
            
                # Add django_openid app if it isn't already there.
                run "cd #{project_path} && ( [ -d python/django_openid ] || svn co http://django-openid.googlecode.com/svn/trunk/django_openid python/django_openid )"
            end
              #run "cd #{project_path} && ( [ -f python/uuid.py ] || wget -O python/uuid.py http://zesty.ca/python/uuid.py )"

#             run "cd #{project_path} && ( [ -d python/temp-mysql ] || mkdir python/temp-mysql )"
#             run "cd #{project_path}/python/temp-mysql && wget http://easynews.dl.sourceforge.net/sourceforge/mysql-python/MySQL-python-1.2.2.tar.gz && gunzip MySQL-python-1.2.2.tar.gz && tar xvf MySQL-python-1.2.2.tar && cd MySQL-python-1.2.2 && su root" do |ch, stream, out|
#                 cmds = "#{rootpw}\n" + <<-END
# python setup.py install
# exit
# END
#                 ch.send_data cmds if out =~ /^Password/
#                 puts out
#             end
#             #run "rm -rf #{project_path}/python/temp-mysql"

            # Add pyfacebook (as its preferred package name, "facebook") if it isn't already there
            if site_features.include?('facebook_connect')
                run "cd #{project_path} && ( [ -d python/facebook ] || svn co http://pyfacebook.googlecode.com/svn/trunk/facebook python/facebook )"
            end
            
            run "cd #{project_path} && ( [ -d python/temp-docutils ] || mkdir python/temp-docutils )"
            run "cd #{project_path}/python/temp-docutils && ( [ -d ../docutils ] || ( wget http://docutils.sourceforge.net/docutils-snapshot.tgz && tar xvf docutils-snapshot.tgz && cd docutils && python setup.py install --install-purelib=#{project_path}/python --install-scripts=#{project_path}/python ) )"
            run "rm -rf #{project_path}/python/temp-docutils"
            
            logger.info "Installation complete. If you haven't done so already, you will need to configure the application by running 'cap deploy:dbsetup'."
        
            #run "mysql -uadmin -p"
            #mysql> create database noosphere_djangonaut_test;
            #mysql> grant all privileges on noosphere_djangonaut_test.* to djangonauttest@localhost identified by '**password goes here**';

            #mysql> exit

            #export PYTHONPATH=..
            #python nooengine/manage.py syncdb
        end
    end
    
    desc "Set up passwordless public-key authentication from the local host"
    task :pubkeysetup do
        set(:rootpw) do
            Capistrano::CLI.ui.ask("Please enter the root password: ")
        end
        default_run_options[:pty] = true # or else you'll get "sorry, you must have a tty to run sudo"
        run "[ -d .ssh ] || ( export SAVEDUSER=`whoami` && su root )" do |ch, stream, out| #[ -d ~/.xssh ] ||
            cmds = <<-END
mkdir .ssh
chown $SAVEDUSER:root .ssh
chmod 700 .ssh
exit
END
        
            if out =~ /^Password/
                ch.send_data "#{rootpw}\n" + cmds
            end
        end
        put File.read(File.expand_path('~/.ssh/id_rsa.pub')), '.ssh/additional_authorized_key.temp'
        run "cat ~/.ssh/additional_authorized_key.temp >> ~/.ssh/authorized_keys"
        run "chmod 600 ~/.ssh/authorized_keys"
        run "rm ~/.ssh/additional_authorized_key.temp"
    end

    desc "Set up database for a site from scratch"
    task :dbsetup, :roles => :web do
        project_homes.each do |project_path|
            default_run_options[:pty] = true # or else you'll get "sorry, you must have a tty to run sudo" 
            set(:dbname) do
                Capistrano::CLI.ui.ask("Please enter the new database name: ")
            end
            set(:dbuid) do
                Capistrano::CLI.ui.ask("Please enter the new database userid: ")
            end
            set(:dbpw) do
                Capistrano::CLI.ui.ask("Please enter the new database password: ")
            end
            set(:dbadminpw) do
                Capistrano::CLI.ui.ask("Please enter the database admin password (Plesk password): ")
            end
            
            run "mysql -uadmin -p" do |ch, stream, out|
                if out
                    puts out
                end
                if out =~ /^Enter password:/
                    ch.send_data "#{dbadminpw}\n"
                end
                if out =~ /mysql>/
                    cmds = <<-END
create database #{dbname};
grant all privileges on #{dbname}.* to #{dbuid}@localhost identified by '#{dbpw}';
exit;
END
                    ch.send_data cmds
                    puts cmds
                end
            end
            
            localsettings = <<-END
# Items here override settings.py. This file is excluded from the repository,
# so it can include secrets like passwords.
DEBUG = False
DATABASE_NAME = '#{dbname}'
DATABASE_USER = '#{dbuid}'
DATABASE_PASSWORD = '#{dbpw}'

# Amazon S3 connection info
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_S3_BACKUP_BUCKET = ''

FORCE_AGGREGATE_CSS = False
FORCE_AGGREGATE_JS = False

SOLR_SERVER = 'localhost'    # empty value means Solr search server will not be used
SOLR_PORT = 8983

VALIDATOR = False

THEME_NAME = 'default'

END
            #put localsettings, "#{project_path}/python/nooengine/local_settings.py"
            put localsettings, (project_path[2..-1] or '.') + "/work/temp_local_settings.py"
            run "[ -d #{project_path}/python/project ] && [ ! -f #{project_path}/python/project/local_settings.py ] && mv #{project_path}/work/temp_local_settings.py #{project_path}/python/project/local_settings.py"
            run "[ ! -d #{project_path}/python/project ] && [ ! -f #{project_path}/python/nooengine/local_settings.py ] && mv #{project_path}/work/temp_local_settings.py #{project_path}/python/nooengine/local_settings.py"
            
            #run "sed -e 's/(DATABASE_NAME *= *\\\\')\\w*\\\\'/\\\\1#{dbname}/\\\\'' <#{project_path}/python/local_settings.py >#{project_path}/local_settings.py"
            
            # The following lines will only work on nooengine sites. They
            # allow updating local_settings.py after it's already been created.
            run "[ -d #{project_path}/python/nooengine ] && python #{project_path}/python/nooengine/noomake/change_local_setting.py DATABASE_NAME \"\'#{dbname}\'\""
            run "[ -d #{project_path}/python/nooengine ] && python #{project_path}/python/nooengine/noomake/change_local_setting.py DATABASE_USER \"\'#{dbuid}\'\""
            run "[ -d #{project_path}/python/nooengine ] && python #{project_path}/python/nooengine/noomake/change_local_setting.py DATABASE_PASSWORD \"\'#{dbpw}\'\""

            run "PYTHONPATH=#{project_path}/python PYTHON_EGG_CACHE=#{project_path}/python-egg-cache python #{project_path}/python/nooengine/manage.py syncdb --noinput"
        end
    end
    
    desc "Configure Apache and set a theme"
    task :apachesetup, :roles => :web do
        #set(:theme) do
        #    Capistrano::CLI.ui.ask("Please enter the theme name [e.g. default, dogfood]: ")
        #end
        set(:rootpw) do
            Capistrano::CLI.ui.ask("Please enter the root password: ")
        end
        unless variables.include?(:django_only)
            set :django_only, false
        end
        unless variables.include?(:site_features)
            if :django_only
                set :site_features, ['project']
            else
                set :site_features, ['nooengine_full', 'themes', 'facebook_connect', 'openid']
            end
        end
        
        default_run_options[:pty] = true # or else you'll get "sorry, you must have a tty to run sudo" 
        
        project_homes.each do |project_path|
            short_name = project_path.gsub('~', '').gsub('/subdomains/', '').gsub('^/', '').gsub('/', '.')
            conf=<<-END
RewriteMap local-settings-override txt:#{project_path}/python/project/local_settings_override.txt
Alias /site_media #{project_path}/python/nooengine/media
Alias /admin_media #{project_path}/python/django/contrib/admin/media
Alias /php #{project_path}/python/nooengine/php

# enable mod_expires, so Expires headers will be sent to the browser
ExpiresActive On

# instruct mod_deflate on how to handle poor browsers
BrowserMatch ^Mozilla/4 gzip-only-text/html
BrowserMatch ^Mozilla/4\.0[678] no-gzip
BrowserMatch \bMSIE !no-gzip !gzip-only-text/html

AddHandler fcgid-script .php5 .php
<Location /forums/feeds>
  Satisfy Any
  Allow From All
</Location>
<IfModule wsgi_module>
  WSGIDaemonProcess #{short_name}SHORTSITENAME threads=15 python-path=#{project_path}/python:#{project_path}/python/project:#{project_path}/python/nooengine python-eggs=#{project_path}/python-egg-cache stack-size=524888 inactivity-timeout=86400 display-name=%{GROUP} user=apache group=apache maximum-requests=1000
  WSGIProcessGroup #{short_name}SHORTSITENAME
  WSGIScriptAlias / #{project_path}/python/nooengine/start-wsgi.py
</IfModule>
<Location />
  <IfModule !wsgi_module>
    SetEnv DJANGO_SETTINGS_MODULE nooengine.settings
    SetEnv PYTHON_EGG_CACHE #{project_path}/python-egg-cache
    <IfModule mod_python.c>
      SetHandler python-program
      PythonHandler django.core.handlers.modpython
      PythonDebug On
      PythonPath "['#{project_path}/python','#{project_path}/python/project','#{project_path}/python/nooengine'] + sys.path"
    </IfModule>
    <IfModule !mod_python.c>
      <IfModule mod_fcgid.c>
        Options ExecCGI FollowSymLinks
        AddHandler fcgid-script .fcgi
        FCGIWrapper "/usr/bin/env PYTHONPATH='#{project_path}/python:#{project_path}/python/project:#{project_path}/python/nooengine' /usr/bin/python #{project_path}/python/project/manage.py runfcgi method=threaded daemonize=false" .fcgi
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteRule ^(.*)$ dispatch.fcgi [QSA,L]
      </IfModule>
    </IfModule>
  </IfModule>
  AuthName "Restricted Access"
  AuthUserFile #{project_path}/htpasswd
  AuthGroupFile /dev/null
  AuthType Basic
  require valid-user
</Location>
<Location /admin_media>
  SetHandler None
</Location>
<Location /site_media>
  SetHandler None
  SetOutputFilter DEFLATE
</Location>
<Location /forums/feeds>
</Location>
<Location /php>
  SetHandler None
  SetOutputFilter DEFLATE
  #AddHandler php5-script .php
  AddHandler fcgid-script .php
</Location>
RewriteEngine On
RewriteCond #{project_path}/python/project/themes/${local-settings-override:THEME_NAME|default}/media/$1 -f
RewriteRule ^/site_media/(.*)$ #{project_path}/python/project/themes/${local-settings-override:THEME_NAME|default}/media/$1 [L]
RewriteCond #{project_path}/python/project/media/$1 -f
RewriteRule ^/site_media/(.*)$ #{project_path}/python/project/media/$1 [L]
RewriteCond #{project_path}/python/nooengine/themes/${local-settings-override:THEME_NAME|default}/media/$1 -f
RewriteRule ^/site_media/(.*)$ #{project_path}/python/nooengine/themes/${local-settings-override:THEME_NAME|default}/media/$1 [L]
<Directory #{project_path}/python/project/media>
  ExpiresByType text/html "access plus 1 day"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/x-javascript "access plus 1 year"
  ExpiresByType image/gif "access plus 1 month"
  ExpiresByType image/jpg "access plus 1 month"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/png "access plus 1 month"
</Directory>
<Directory #{project_path}/python/nooengine/media>
  ExpiresByType text/html "access plus 1 day"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/x-javascript "access plus 1 year"
  ExpiresByType image/gif "access plus 1 month"
  ExpiresByType image/jpg "access plus 1 month"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/png "access plus 1 month"
</Directory>
<Directory #{project_path}/python/nooengine/php>
  #php_admin_flag engine on
  AddHandler fcgid-script .php
  FCGIWrapper /usr/bin/php-cgi .php
  Options ExecCGI
  ExpiresByType text/html "access plus 1 day"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/x-javascript "access plus 1 year"
  ExpiresByType image/gif "access plus 1 month"
  ExpiresByType image/jpg "access plus 1 month"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/png "access plus 1 month"
</Directory>
<Directory #{project_path}/httpdocs/mailinglist>
  AddHandler fcgid-script .php
  FCGIWrapper /usr/bin/php-cgi .php
  Options ExecCGI
</Directory>
<Location /mailinglist>
  SetHandler None
  AddHandler fcgid-script .php
</Location>
END
            #run "python #{project_path}/python/nooengine/noomake/change_local_setting.py THEME_NAME \"\'#{theme}\'\""
            
            put conf, "work/temp.conf"
            if project_path[0..0] == '~'
                # expand paths-- Apache paths must be absolute
                run "sed -i \"s|~/|`pwd`/|g\" work/temp.conf"
            end
            run "sed -i \"s|SHORTSITENAME|`basename \\`pwd\\``|g\" work/temp.conf"
            
            #sudo "mv -f work/temp.conf #{project_path}/conf/vhost.conf"
            # sudo won't work for this due to sudoers restrictions, so we use su root instead
            run "su root -c \"mv -f work/temp.conf `dirname #{project_path}/conf`/conf/vhost.conf\"" do |ch, stream, out|
                ch.send_data "#{rootpw}\n" if out =~ /^Password/
            end
            
            # Make sure local_settings_override.txt exists and is readable &
            # writable by the web server user. Currently this means 'other'
            # has read & write (permission mode 666), since the web server user
            # isn't the owner nor a member of psacln, the default group.
            run "touch #{project_path}/python/project/local_settings_override.txt"
            run "su root -c \"chmod 0666 `dirname #{project_path}/conf`/python/project/local_settings_override.txt\"" do |ch, stream, out|
                ch.send_data "#{rootpw}\n" if out =~ /^Password/
            end
            
            deploy.restart_apache
        end
    end

    desc "Configure Apache and set a theme"
    task :apacheminimalsetup, :roles => :web do
        #set(:theme) do
        #    Capistrano::CLI.ui.ask("Please enter the theme name [e.g. default, dogfood]: ")
        #end
        set(:rootpw) do
            Capistrano::CLI.ui.ask("Please enter the root password: ")
        end
        
        default_run_options[:pty] = true # or else you'll get "sorry, you must have a tty to run sudo" 
        
        project_homes.each do |project_path|
            project_checkout_path = project_path + '/python/project'
            short_name = project_path.gsub('~', '').gsub('/subdomains/', '').gsub('^/', '').gsub('/', '.')
            conf=<<-END
Alias /site_media #{project_checkout_path}/media
Alias /admin_media #{project_path}/python/django/contrib/admin/media

# enable mod_expires, so Expires headers will be sent to the browser
ExpiresActive On

# instruct mod_deflate on how to handle poor browsers
BrowserMatch ^Mozilla/4 gzip-only-text/html
BrowserMatch ^Mozilla/4\.0[678] no-gzip
BrowserMatch \bMSIE !no-gzip !gzip-only-text/html

<IfModule wsgi_module>
  WSGIDaemonProcess #{short_name}SHORTSITENAME threads=15 python-path=#{project_path}/python:#{project_checkout_path} python-eggs=#{project_path}/python-egg-cache stack-size=524888 inactivity-timeout=86400 display-name=%{GROUP} user=apache group=apache maximum-requests=1000
  WSGIProcessGroup #{short_name}SHORTSITENAME
  WSGIScriptAlias / #{project_checkout_path}/start-wsgi.py
</IfModule>
<Location />
  <IfModule !wsgi_module>
    SetEnv DJANGO_SETTINGS_MODULE settings
    SetEnv PYTHON_EGG_CACHE #{project_path}/python-egg-cache
    <IfModule mod_python.c>
      SetHandler python-program
      PythonHandler django.core.handlers.modpython
      PythonDebug On
      PythonPath "['#{project_path}/python','#{project_checkout_path}'] + sys.path"
    </IfModule>
    <IfModule !mod_python.c>
      <IfModule mod_fcgid.c>
        Options ExecCGI FollowSymLinks
        AddHandler fcgid-script .fcgi
        FCGIWrapper "/usr/bin/env PYTHONPATH='#{project_path}/python:#{project_checkout_path}' /usr/bin/python #{project_checkout_path}/manage.py runfcgi method=threaded daemonize=false" .fcgi
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteRule ^(.*)$ dispatch.fcgi [QSA,L]
      </IfModule>
    </IfModule>
  </IfModule>
  AuthName "Restricted Access"
  AuthUserFile #{project_path}/htpasswd
  AuthGroupFile /dev/null
  AuthType Basic
  require valid-user
</Location>
<Location /admin_media>
  SetHandler None
</Location>
<Location /site_media>
  SetHandler None
  SetOutputFilter DEFLATE
</Location>
<Directory #{project_checkout_path}/media>
  ExpiresByType text/html "access plus 1 day"
  ExpiresByType text/css "access plus 1 year"
  ExpiresByType text/javascript "access plus 1 year"
  ExpiresByType application/x-javascript "access plus 1 year"
  ExpiresByType image/gif "access plus 1 month"
  ExpiresByType image/jpg "access plus 1 month"
  ExpiresByType image/jpeg "access plus 1 month"
  ExpiresByType image/png "access plus 1 month"
</Directory>
END
            #run "python #{project_path}/python/nooengine/noomake/change_local_setting.py THEME_NAME \"\'#{theme}\'\""
            
            put conf, "work/temp.conf"
            if project_path[0..0] == '~'
                # expand paths-- Apache paths must be absolute
                run "sed -i \"s|~/|`pwd`/|g\" work/temp.conf"
            end
            run "sed -i \"s|SHORTSITENAME|`basename \\`pwd\\``|g\" work/temp.conf"
            
            #sudo "mv -f work/temp.conf #{project_path}/conf/vhost.conf"
            # sudo won't work for this due to sudoers restrictions, so we use su root instead
            run "su root -c \"mv -f work/temp.conf `dirname #{project_path}/conf`/conf/vhost.conf\"" do |ch, stream, out|
                ch.send_data "#{rootpw}\n" if out =~ /^Password/
            end
            
            # Make sure local_settings_override.txt exists and is readable &
            # writable by the web server user. Currently this means 'other'
            # has read & write (permission mode 666), since the web server user
            # isn't the owner nor a member of psacln, the default group.
            run "touch #{project_checkout_path}/local_settings_override.txt"
            run "su root -c \"chmod 0666 `dirname #{project_checkout_path}/ignored`/local_settings_override.txt\"" do |ch, stream, out|
                ch.send_data "#{rootpw}\n" if out =~ /^Password/
            end
            
            deploy.restart_apache
        end
    end
end

# info:httpd_mem. See
# http://nubyonrails.com/articles/tips-for-upgrading-to-capistrano-2
namespace :info do
  desc "Get top 10 httpd processes by real memory usage" 
  task :httpd_mem, :roles => [:web] do
    run <<-CMD
    ps axcmo pid,rsz,command | grep httpd | awk '{LIMIT = 1; if ($2 > LIMIT) printf $2/1024 " MB  \n"}' | sort -rn | head -n10
    CMD
  end
end