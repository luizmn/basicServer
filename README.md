#README
##Accessing the server
To access the web catalog:  
[https://www.awstestmonth.tk/](https://www.awstestmonth.tk/)  
To access the catalog server:  
IP: 18.213.152.131  
Port: 2200  
User: grader  

To access the portfolio demo:  
[http://www.lmnportfolio.tk/](http://www.lmnportfolio.tk/)  


##Configuring a Linux Web server

This file will give you simple instructions to configure a basic web server instance with the previous Catalog Web page project from Udacity.

##Public
These instructions were made for people with some previous knowledge in Linux.
If you do not have any knowledge, please watch/read the tutorials in the instructor notes.

##Pre-requisites

In order to create the server, we assume you have access to a virtual machine in the cloud or physically in your PC/Mac/Server.
This instruction was made using a free Amazon Lightsail instance. If you wish to create one, follow this [link](https://cloudacademy.com/blog/how-to-set-up-your-first-amazon-lightsail/).
For convenience/easy of use (and required to use with a domain), after configuring, create and assign a [static IP](https://lightsail.aws.amazon.com/ls/docs/en/articles/lightsail-create-static-ip) to your instance.


##Requirements
In order to set up this web server you will need:  
* Ubuntu 18  
* Apache2  
* libapache2-mod-wsgi  
* Python 2.7  
* SQLAlchemy  
* PostgreSQL  
* UFW Firewall  
* python-psycopg2  
* python-requests  
* oauth2client  
* certbot-auto (optional)  
* libapache2-modsecurity (optional)  
* libapache2-mod-evasive (optional)  
* Apache2Buddy script (optional)  

All python requirements can be found in the file **requirements.txt**

##First things first
###Updating the system
Afters installing and configuring the system, make sure you are using the latest packages/sources.  
Use   ```$  sudo apt-get update -y``` to download the package lists from the repositories and "update" them to get information on the newest versions of packages and their dependencies.     
Then run ```$  sudo apt-get upgrade -y```

**Note**: The ```-y```option is used to automatic say "yes" to prompts; assume "yes" as answer to all prompts and run non-interactively.

**Note 2:** Some people talk about enabling automatic updates/upgrades but, in a real production server, this option should not be enabled since some updates could break your software/system.
All updates/upgrades must be tested in another server prior to update the production server. 
####Create a user called 'grader' to access the server
```$ adduser grader```  

Ubuntu will ask for a password and some information like name, phone, etc. 

After filling the information you need to add the newly created user to the _sudo_ group.
```$ usermod -aG sudo 'username'```  
In this case, run   ```$ usermod -aG sudo grader```  
Test sudo access on new user account.  
Switch to the new user account using  
```$ su - grader```

Verify that you can use sudo by prepending "sudo" to the command that you want to run with superuser privileges.
Ex.: ```$ sudo ls -la /root```

If everything is correct, the user grader will be able to list the contents of the root folder. 


##Securing SSH
If you would like to know more, you can check this article [Securing SSH server on Ubuntu](https://devops.profitbricks.com/tutorials/secure-the-ssh-server-on-ubuntu/)
But two of the most basic common security guidelines are changing the port and disable SSH root login. 
####Change SSH port
Change SSH port for anything other than 22. Use this [list](http://www.linuxandubuntu.com/home/what-are-ports-how-to-find-open-ports-in-linux) to see what are common used ports in Linux systems to avoid choosing an already used port.

After choosing the new port, it is better to open it in your firewall (if you already have it running), otherwise, you will be locked out. If you do not have a running firewall (check with ```$ sudo ufw status```), the basic configuration will be showed later.

To change the port, run ```$ sudo nano -w /etc/ssh/sshd_config``` to open the sshd_config file. Then look at the line containing the value "Port 22" and change the number 22 with your desired port.  

Save the file, close it and restart the service using  
 ```$ sudo systemctl restart sshd```  
 
To check if the port has changed use  
```$ sudo systemctl status sshd```  

Look in the result for the line "Server listening on :: port XX" (XX will be the chosen port).

**Important:** After you change the port and restart the service, you will be disconnected from remote server.

To access again, use through your SSH client following these [instructions](https://docs.aws.amazon.com/quickstarts/latest/vmlaunch/step-2-connect-to-instance.html#sshclient).

####Disabling SSH root login
Disable root login

A common attack is to attempt to use root to log into a server with SSH. To avoid this risk, disable root SSH login by changing PermitRootLogin from without-password, prohibit-password or yes to:

```PermitRootLogin no```

####Hide last login

You can hide last login user by editing the following line.

```PrintLastLog no```

###How To Set Up SSH Keys 

Create the RSA Key Pair in the client (usually, your computer):  
```$ sudo ssh-keygen -t rsa```  
It will ask you where to store the file:
> Enter file in which to save the key (/home/user/.ssh/id_rsa):
You can just hit _enter_ to save the file to the home user directory.   
Then you will be asked to enter a passphrase. You can press _enter_ for no passphrase but it is **recommended** to enter one because the security of a key, no matter how encrypted, still depends on the fact that it is not visible to anyone else. 
If a passphrase-protected private key fall into an unauthorized users possession, they will be unable to log in to its associated accounts until they figure out the passphrase, buying the hacked user some extra time. The only downside, of course, to having a passphrase, is then having to type it in each time you use the key pair.  

The public key is now located in _/home/user/.ssh/id_rsa.pub_. The private key (identification) is now located in 
> /home/user/.ssh/id_rsa

Now you have to copy the public key to the machine's authorized_keys file. You can do it in three ways:

Using ssh-copy-id:
 ```$ sudo ssh-copy-id user@host-ip```   

Paste in the keys using SSH:
 ```$ sudo cat ~/.ssh/id_rsa.pub | ssh user@host-ip "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >>  ~/.ssh/authorized_keys"```  

At last, simply open id_rsa.pub file (client), copy the content and paste inside /.ssh/authorized_keys file (host machine)

 
[How To Set Up SSH Keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2)
##Configuring the firewall

You may check this tutorial ["Setting up the ufw firewall"](https://www.digitalocean.com/community/tutorials/how-to-setup-a-firewall-with-ufw-on-an-ubuntu-and-debian-cloud-server) to understand more of the firewall configuration but in order to make our server work you will have to run just some  commands:  
```$ sudo apt-get install ufw```  

As a basic firewall configuration, we have to deny all incoming connections and allow all outgoing connections. _What does this means!?_ It means anyone trying to reach your server will not be able to connect, but  any application within the server would be able to reach the outside world. 


```$ sudo ufw default deny incoming```

and

```$ sudo ufw default allow outgoing```

To make your server accessible you will have to open the ports below:  
HTTP: 80  
HTTPS: 443  
SSH: 2200 (or the port you have chosen for the service)  
POSTGRES: 5432  

**Run:**  

```$ sudo ufw allow http```  
```$ sudo ufw allow 2200/tcp```  
```$ sudo ufw allow ntp```
```$ sudo ufw allow postgres```  

After running one command the messages below will be displayed:  
```Rules updated```  
```Rules updated (v6)```

After configuring the Firewall, enable with  
```$ sudo ufw enable```

To check firewall status run  
```$ sudo ufw status```

##Configuring NTP
[NTP](http://www.ntp.org/ntpfaq/NTP-s-def.htm) stands for Network Time Protocol, and it is an Internet protocol used to synchronize the clocks of computers to some time reference. NTP is an Internet standard protocol originally developed by [Professor David L. Mills](http://www.ntp.org/ntpfaq/NTP-a-faq.htm#AU-DLM )at the University of Delaware.

For more info, check [NTP](http://www.ntp.org/ntpfaq/NTP-s-def.htm) site.  

Install NTP:  
```$ sudo apt-get install ntp```

```$ sudo timedatectl set-ntp on```

Use your browser to navigate to [NTP Pool Project](http://www.pool.ntp.org/zone/@) and find the closest NTP server pool to your location.

Once you have the list, open the NTP server's main configuration

```$ sudo nano /etc/ntp.conf```

Replace lines:

> pool 0.ubuntu.pool.ntp.org iburst  
> pool 1.ubuntu.pool.ntp.org iburst  
> pool 2.ubuntu.pool.ntp.org iburst  
> pool 3.ubuntu.pool.ntp.org iburst  

With the list obtained from the NTP pool Project. 
Save the file and restart your NTP server: 
```$ sudo systemctl restart ntp```

##Install Apache 2 
After updating the sources install Apache using:     
 ```$ sudo apt-get install apache2 ```  

Next, adjust the firewall to allow Apache on port 80 (since Apache is not configured for using SSL, allowing just this port will do).  
```$ sudo ufw allow 'Apache'```

The better way to test Apache is running it and accessing in the browser.  
Use  
```$ sudo systemctl start apache2```   
Check if it is running with  
```$ sudo systemctl status apache2```  
Then go to your browser and type http://server_ip  
If everything works you should see the default Ubuntu 18.04 Apache web page:
![Apache](https://assets.digitalocean.com/articles/how-to-install-lamp-ubuntu-16/small_apache_default.png) 

Install _libapache2-mod-wsgi_ which is an Apache module that provides a WSGI (Web Server Gateway Interface, a standard interface between web server software and web applications written in Python) compliant interface for hosting Python based web applications within Apache.  

```$ sudo apt-get install libapache2-mod-wsgi```

For convenience, do not forget to set up Apache2 to automatically start at boot with  
```$ sudo systemctl enable apache2```

If you want more information you can check this [tutorial](https://www.digitalocean.com/community/tutorials/how-to-install-the-apache-web-server-on-ubuntu-18-04) on installing Apache on Ubuntu 18.
 
##Python 2.7 
Install Python 2:  
```$ sudo apt-get install python```  
Install Python Pip to manage packages:  
```$ sudo apt-get install python-pip```

##Flask
As this project was written using a Python microframework called [Flask](http://flask.pocoo.org/) we also need to install it:  
```$ sudo apt-get install flask```


##PostgreSQL
Install PostgreSQL  
```$ sudo apt-get install postgresql```

After installing, change the user to postgres:  
```$ su - postgres```

Create User in Postgres  
```$ createuser webaccess```

Create Database  
```$ createdb partscatalog```

Access the postgres Shell  
```$ psql``` (enter the password for postgresql)

Provide the privileges to the postgres user

```$ alter user webaccess with encrypted password 'webaccess';```
```$ grant all privileges on database partscatalog to webaccess;```

##Git
Install Git to download/update the project:  
```$ sudo apt-get install git```

##Download project from Github
You have two options for downloading the project:  
###Download the zipped folder directly from github site. 
Create a folder or just go to your home folder and use  
```$ wget https://github.com/luizmn/basicServer/archive/master.zip```  
After downloading the file, extract it´s contents  
Example:```$ unzip master.zip```

###Clone/download via a git client;  
Use  
```$ git clone https://github.com/luizmn/basicServer.git```  
It will copy the folder basicServer to your desired place. 

###Setting up the catalog app
Enter the folder and copy the subfolder called _carparts_ to Apache's document root folder with  
```$ sudo cp -R carparts/ /var/www/html/.```  
After that, change the permission  
```sudo chown -R  /var/www/html/carparts```  
and the owner of the file/folder:
```sudo chown -R www-data:www-data /var/www/html/carparts```

###Setting Up Virtual Hosts
Create a new Virtual Host configuration file by copying default file.

```$ cd /etc/apache2/sites-available/```  
```$ sudo cp 000-default.conf carparts.com.conf```

Edit VirtualHost configuration: 
```$ sudo nano -w carparts.com.conf```

The file will look like this 

> `<VirtualHost *:80>`   
>     `ServerAdmin admin@example.com`   
>     `ServerName example.com`   
>     `ServerAlias www.example.com`   
>     `DocumentRoot /var/www/example.com/html` 
>     `ErrorLog ${APACHE_LOG_DIR}/error.log` 
>     `CustomLog ${APACHE_LOG_DIR}/access.log combined` 
> `</VirtualHost>`

Edit the file and add the site information:
> `<VirtualHost *:80>`   
>     `ServerAdmin admin@emailprovider.com`   
>     `ServerName carparts.com`   
>     `ServerAlias www.carparts.com`   
>     `DocumentRoot /var/www/html/carparts` 
>     `ErrorLog ${APACHE_LOG_DIR}/error.log` 
>     `CustomLog ${APACHE_LOG_DIR}/access.log combined` 
> `#The line below is the alias of the app`
> `WSGIScriptAlias / /var/www/html/carparts/carparts.wsgi`   
> `</VirtualHost>` 

Save and close the file.  

**Note**: www.carparts.com only can be accessed _locally_ if you edit the _hosts_ file in your computer.  
In _/etc/hosts_ put the domains you want:  
`127.0.0.1 www.carparts.com`  
Save and close the file.

Enable the file with the a2ensite tool:

```$ sudo a2ensite carparts.com.conf```

Disable the default site defined in 000-default.conf:

```$ sudo a2dissite 000-default.conf```

Test for configuration errors:

```$ sudo apache2ctl configtest```

You should see the following output:

> Output  
> Syntax OK  

Finally, restart Apache
```$ sudo systemctl restart apache2```

And access in your browser:
> http://localhost  
or  
> http://your-server-ip  
or  
> http://www.carparts.com
 

Now you will be able to access the catalgo app in your browser.

The catalog app has a login page that uses Google and Facebook authentication for inserting items.
Before using the login page you should create your [Google](https://developers.google.com/identity/protocols/OAuth2) and [Facebook](https://developers.facebook.com/docs/facebook-login/web) access and change the __carparts/templates/login.html__ file to insert your own codes. 

The steps below are optional but will ease the access and provide some security for external users.
 
##Get a free domain (Optional)
You can test your site in internet with:  
* Your public IP provided by Amazon Lightsail;  
* A free wildcard DNS from [xip.io](http://xip.io/);  
* A free custom domain registered with [Dot.tk](http://www.dot.tk/);  

After registering your domain, you should edit the VirtualHost file in _/etc/apache2/sites-available/_ and add your new domain, then restart Apache.  


##Secure Apache with Let's Encrypt (Optional)
_"[Let’s Encrypt](https://letsencrypt.org/) is a free, automated, and open Certificate Authority. 
To enable HTTPS on your website, you need to get a certificate (a type of file) from a Certificate Authority (CA). Let’s Encrypt is a CA. In order to get a certificate for your website’s domain from Let’s Encrypt, you have to demonstrate control over the domain. With Let’s Encrypt, you do this using software that uses the ACME protocol, which typically runs on your web host."_  
Currently, the entire process of obtaining and installing a certificate is fully automated on both Apache and Nginx.  
To setup Certbot in Ubuntu 18 follow these [simple steps](https://certbot.eff.org/lets-encrypt/ubuntuother-apache)

After Using Let's Encrypt, don't forget to open the new port in firewall with:  
```$ sudo ufw allow https``` 

##Configure Apache to host multiple sites (optional)
Virtual Hosting refers to running multiple domains (or multiple websites) on a single server. The best uses of Virtual Hosting can be seen on shared hosting servers, where thousands of websites hosted on a single server and share the single system resources.

Create a new Virtual Host configuration file by copying default file.

```$ cd /etc/apache2/sites-available/```  
```$ sudo cp 000-default.conf site2.example.com.conf```

**Note** site2.example.com.conf name should be changed to reflect your new site.

Edit the file __site2.example.com.conf__ in you preferred editor as you did previously with the catalog file.
```$ sudo nano -w site2.example.com.conf```  

Change these lines and add your own information about the site. 
> ServerAdmin webmaster@site1.example.com
> ServerName site1.example.com
> DocumentRoot /var/www/html/site1.example.com/

Enable the file with the a2ensite tool:

```$ sudo a2ensite site2.example.com.conf```

Test for configuration errors:

```$ sudo apache2ctl configtest```

You should see the following output:

> Output  
> Syntax OK  

Finally, restart Apache
```$ sudo systemctl restart apache2```
        
If you want more information you can check this [tutorial](https://www.ostechnix.com/configure-apache-virtual-hosts-ubuntu-part-1/) on creating Apache VirtualHost on Ubuntu 18.

###Secure your Apache with ModSecurity (optional)

ModSecurity is an Apache module used for security, that basically acts as a firewall, and it monitors your traffic. To install it, run:

```$ sudo apt-get install libapache2-modsecurity```

And restart Apache:

```$ sudo systemctl restart apache2```

ModSecurity comes with a default setup that’s good enough by itself, but if you want to extend it, you can use the [OWASP rule set](https://www.owasp.org/index.php/Category:OWASP_ModSecurity_Core_Rule_Set_Project).

Source [ThisHosting.Rocks](https://thishosting.rocks/how-to-install-optimize-apache-ubuntu/)

###Block DDoS attacks using the mod_evasive module (optional)

You can use the mod_evasive module to block and prevent DDoS attacks on your server, though it’s debatable how useful it is in preventing attacks. To install it, use the following command:

```$ sudo apt-get install libapache2-mod-evasive```

By default, mod_evasive is disabled, to enable it, edit the following file:

```$ sudo nano /etc/apache2/mods-enabled/evasive.conf```

And uncomment all the lines (remove #) and configure it per your requirements. You can leave everything as-is if you don’t know what to edit.  

Create a log file:

```$ sudo mkdir /var/log/mod_evasive```  
```$ sudo chown -R www-data:www-data /var/log/mod_evasive```  

Restart Apache for the changes to take effect:

```$ sudo systemctl restart apache2```

Source: [ThisHosting.Rocks](https://thishosting.rocks/how-to-install-optimize-apache-ubuntu/)

###Optimize Apache with the Apache2Buddy script (optional)

Apache2Buddy is a script that will automatically fine-tune your Apache configuration. The only thing you need to do is run the following command and the script does the rest automatically:

```$ sudo curl -sL https://raw.githubusercontent.com/richardforth/apache2buddy/master/apache2buddy.pl | sudo perl```

You may need to install curl if you don’t have it already installed. Use the following command to install curl:

```$ sudo apt-get install curl``` 
 
Source: [ThisHosting.Rocks](https://thishosting.rocks/how-to-install-optimize-apache-ubuntu/)  

##References
* [How To Set Up SSH Keys](https://www.digitalocean.com/community/tutorials/how-to-set-up-ssh-keys--2)
* [Installing Apache 2 on Ubuntu 18](https://www.digitalocean.com/community/tutorials/how-to-install-the-apache-web-server-on-ubuntu-18-04)
* [Setting up the ufw firewall](https://www.digitalocean.com/community/tutorials/how-to-setup-a-firewall-with-ufw-on-an-ubuntu-and-debian-cloud-server)
* [Amazon Lightsail: How to set up your first instance](https://cloudacademy.com/blog/how-to-set-up-your-first-amazon-lightsail/)
* [Creating a sudo user on Ubuntu](https://www.digitalocean.com/community/tutorials/how-to-create-a-sudo-user-on-ubuntu-quickstart)
* [NTP Server configuration](https://linuxconfig.org/ntp-server-configuration-on-ubuntu-18-04-bionic-beaver-linux)
* [Certbot install] (https://certbot.eff.org/lets-encrypt/ubuntuother-apache)
* [Dot.tk - Free Domain](http://www.dot.tk/)
* [Create a static IP and attach it to an instance in Amazon Lightsail](https://lightsail.aws.amazon.com/ls/docs/en/articles/lightsail-create-static-ip)
* [Auto-Renew for Let’s Encrypt SSL Certificates (Apache)](https://www.onepagezen.com/letsencrypt-auto-renew-certbot-apache/)
* [Let’s Encrypt](https://letsencrypt.org/)
* [Configure Apache Virtual Hosts In Ubuntu 18.04 LTS](https://www.ostechnix.com/configure-apache-virtual-hosts-ubuntu-part-1/)
* [Install and Optimize Apache on Ubuntu](https://thishosting.rocks/how-to-install-optimize-apache-ubuntu/)
