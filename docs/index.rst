.. _djangoauthfogbugz:

Django-Auth-FogBugz
===============================================
This authentication backend enables a Django project to authenticate against
any FogBugz (http://www.fogcreek.com/fogbugz/) server.

To use it, add :py:class:`.django_auth_fogbugz.backend.FogBugzBackend` to
``AUTHENTICATION_BACKENDS``. Additional functionality can be enabled if you
add ``django_auth_fogbugz`` to ``INSTALLED_APPLICATIONS``;
see :ref:`fogbugzprofile` for more information.

This has been tested with Django 1.3, 1.4 and 1.5-alpha w/ custom user model,
under python 2.6 and 2.7.

.. WARNING:: It is strongly recommended that you use an SSL (https) connection
             to perform authentication against th FogBugz server for security.



.. _config:

Basic Configuration
--------------------------------------
Here are a few examples of the most basic configurations. Please see the
:ref:`settings` section and the available :ref:`example` for a complete
description of the available options.
Also see :ref:`understanding` for how authentication with FogBugz works in
general.

**The most basic recommended configuration:**

.. code:: python

    AUTH_FOGBUGZ_SERVER = "https://my_account.fogbugz.com/"

    AUTHENTICATION_BACKENDS = (
        'django_auth_fogbugz.backend.FogBugzBackend',
        'django.contrib.auth.backends.ModelBackend',
    )

**FogBugz with LDAP/Active Directory:**

.. code:: python

    AUTH_FOGBUGZ_SERVER = "https://my_account.fogbugz.com/"

    AUTH_FOGBUGZ_SERVER_USES_LDAP = True
    
    AUTHENTICATION_BACKENDS = (
        'django_auth_fogbugz.backend.FogBugzBackend',
        'django.contrib.auth.backends.ModelBackend',
    )


.. _understanding:

Understanding FogBugz Authentication
--------------------------------------
The FogBugz (http://www.fogcreek.com/fogbugz/) bug tracker uses the e-mail
address of it's users as the username, with case-insensitive matching. This
puts a restriction on the users, that no two can have the same e-mail address.
This is not strictly true. It is possible to have more than one user with
the same e-mail address, but this will cause the login to fail for both users.

Under normal use, this is hard to cause, but FogBugz also
allows for integration with LDAP and Active Directory, and the auto-creation
of users on login when either of these is enabled. This can cause such a
conflict.

When LDAP or AD is used either the LDAP/AD username or the e-mail address may
be used, and again the matching is case-insensitive. For AD users, the
'DOMAIN\' prefix can be used. 

If your FogBugz server is configured for LDAP or Active Directory integration,
and you wish for your Django login to accept those usernames as well, then you
should set :ref:`SERVER_USES_LDAP` to ``True``, but you should be be aware of
the :ref:`djangouser` associated with that.

There are also different classifications of users, where each user can be one
of:

:normal: Basic user.
:administrator: Superuser with full admin access.
:community: Special user that does not use a license, and has limited
            access to Wiki's, Discussion Groups, and maybe filing some bugs.
            This is intended for customer support to allow customers to have
            login's.
:virtual: These are non-login e-mail alias accounts for sendding out e-mails.

Users can also be marked 'inactive' similar to Django.

**django-auth-fogbugz** will allow for login of normal and administrative users.
If :ref:`ALLOW_COMMUNITY` is set to ``True``, then those users will also be
allowed to log in. There is no way to allow for virtual users to be
authenticated. Similarly there is no way to tell the difference between an
authentication failure for a user that is marked 'inactive', a user
that does not exist on the FogBugz server, a virtual user, or
an incorrect password.

You can create the Django users by hand so that only those you want to have
access will be allowed to log in, but you will need to make sure to adhere to
the :ref:`djangouser`.

You can set :ref:`AUTO_CREATE_USERS` to ``True`` to have any user on the
FogBugz server able to log in, and a new Django user will be created on their
first login. Some restrictions may apply if LDAP/AD integration is used.


.. _djangouser:

Django User Restrictions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Due to the way that FogBugz allows for e-mail and optional LDAP or Active
Directory login names in a case-insensitive manner, and due to the new
Django 1.5 User model abstraction, there are restrictions on setting up your
Django users.

Because FogBugz uses the e-mail address as the login, this means that the
e-mail address on the User model must be unique in order to have authentication
to work. The e-mail address matching will be case insensitive.

If you have :ref:`AUTO_CREATE_USERS` set to ``True`` then the username will
be set to be the same as the e-mail address, but will be forced to be
lower-case.

Additionally if your FogBugz server has LDAP or Active Directory authentication
enabled, and you want to allow for logging in with the LDAP/AD username, then
you need to set :ref:`SERVER_USES_LDAP` to ``True``. This will add further
restrictions when hand creating Django users:

* The username must be the LDAP/AD username.
* The username must be without the 'DOMAIN\' prefix for Active Directory.
* The username must be all lowercase.

The need to lowercase is because FogBugz does case insensitive matching on the
username, which could be either the e-mail address or the LDAP/AD username.
The new User Model abstraction in Django 1.5 does not allow for case insentive
matching. to work around this we store the username in lowercase, and lowercase
the login supplied username for matching against the Django model. FogBugz
will still authenticate agains the lower-cased username, and the User model
lookup will match exactly.

Furthermore if you are using :ref:`AUTO_CREATE_USERS` and :ref:`SERVER_USES_LDAP`
together, then the first time a new user logs into Django, they must log in with
their LDAP/AD username. This is due to a limitation of the FogBugz API which
can supply the users e-mail address, but can not supply their LDAP/AD username.
As such we can discover the e-mail address from the LDAP/AD username based
authentication, but not visa-versa. Newly created users will have the username
forced to lowercase.



.. _fogbugzpy:

FogBugz Python API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

FogBugz has an XML API (http://fogbugz.stackexchange.com/fogbugz-xml-api)
for accessing the server, and a python wrapper
FogBugzPy (https://developers.fogbugz.com/default.asp?W199) which is
available on PyPi (http://pypi.python.org/pypi/fogbugz/). 

It is not recommended to store the password in plaintext for repeated
access. Instead, the FogBugz XML API allows for a 30 character session token
generated on a per-session basis (https://developers.fogbugz.com/default.asp?W198#toc_2).
You must explicitly 'logoff' in to clear the token. In this way, you can
generate and store the token on authentication with the username and password
for later FogBugz XML API usage.

Only FogBugz users that are 'administrator' users can perform FogBugz XML API
operations as another user, and back-date actions. Typically for Django
applications, this means storing a token for an administrative user, and using
that to perform operations.

:ref:`djangoauthfogbugz` provides an alternative.
You can use :ref:`ENABLE_PROFILE` and :ref:`ENABLE_PROFILE_TOKEN` to
have the user's login token stored in the :ref:`fogbugzprofile`. With each
new Django login, if a token already exists, it will be cleared, and the new
one will be assigned. This will allow you to perform FogBugz interactions as
the logged in Django user, instead of having to have a perminently stored
administrative user.

.. warning:: Enabling the profile token extension will allow any code with
             access to the user models to have a login authentication token
             for non-expired users. This could allow Django code to access
             the FogBugz server as those users.

See :ref:`fogbugzprofile` for more details.


.. _fogbugzprofile:

FogBugzProfile User Model Extension for FogBugzPy
--------------------------------------------------

This is a django model for storing additional information about the users
which are authenticated with **django-auth-fogbugz**. This uses a OneToOne
relation with the Django User model, and will work in parallel to other
User model extensions. This will also work with the new Django 1.5 custom
User model system.

To enable this you must add ``django_auth_fogbugz`` to your ``INSTALLED_APPS``
setting, as well as set :ref:`ENABLE_PROFILE` to ``True``.

.. py:class:: django_auth_fogbugz.models.FogBugzProfile

    .. py:attribute:: user
    
        :type: OneToOneField
        :description: :py:class:`.django.contrib.auth.models.User` this profile is for.

    .. py:attribute:: ixPerson

        :type: PositiveIntegerField
        :description: The FogBugz id for the user in the FogBugz API.
        
    .. py:attribute:: is_normal
    
        :type: BooleanField
        :description: It the FogBugz user is not a community, administrator, or virtual user, this will be set to ``True``.

    .. py:attribute:: is_community
        
        :type: BooleanField
        :description: If the FogBugz user is a special community user, this will be set to ``True``.
        
    .. py:attribute:: is_administrator
    
        :type: BooleanField
        :description: If the FogBugz user is a special administrator user, this will be set to ``True``.
        
    .. py:attribute:: token
   
        :type: CharField
        :length: 30
        :default: ``''``
        :description: If :ref:`ENABLE_PROFILE_TOKEN` is set to ``TRUE``, then
                      this will contain the FogBugz Authentication token for
                      this user. See :ref:`understanding` for more details.

You can access the members of the :py:class:`FogBugzProfile` directly from the
Django user model (e.g. ``user.fogbugzprofile.is_community``)

The :py:attr:`is_normal`, :py:attr:`is_community` and
:py:attr:`is_administrator` fields will be updated with each Django login.

If :ref:`ENABLE_PROFILE_TOKEN` is set to ``True``, then instead of clearing the
FogBugz XML API token after authentication, it will be stored in the
:class:`FogBugzProfile` accessible from the Django User instance as
``user.fogbugzprofile.token``.

Example of using the :py:class:`FogBugzProfile` with FogBugzPy:


.. code:: python

    import fogbugz
    from django.conf import settings
    from django.shortcuts import render
    from django.contrib.auth.decorators import login_required
    
    
    def my_view(request):
        fb = fogbugz.FogBugz(settings.AUTH_FOGBUGZ_SERVER,
                             request.user.fogbugzprofile.token)
        resp = fb.search(q='assignedTo:"me" status:"Active"',
                         cols="ixBug,sTitle",
                         max=10)
        top_ten = []
        for case in resp.cases.findAll('case'):
             top_ten.append("%s: %s\n" % (case.ixbug.string, 
                                          case.stitle.string.encode('UTF-8')))
                                          
        return render(request, "fogbugz/my_top_ten.html",
                      {'top_ten': top_ten})
                      

See :ref:`fogbugzpy` for links to the FogBugz XML API and FogBugzPy
documentaiton from Frog Creek.

.. note:: If you enable token storage, make sure your SESSION_COOKIE_AGE
          is less than or equal to the FogBugz expiration time (2 weeks,
          same as the django default) and that FogBugz Server
          Configuraition for Authentication logon is set to
          ``"Remember Me" Allowed``.

.. warning:: Enabling the profile token extension will allow any code with
             access to the user models to have a login authentication token
             for non-expired users. This could allow Django code to access
             the FogBugz server as those users.



.. _logging:

Logging
--------------------------------------

:py:class:`.django_auth_fogbugz.backend.FogBugzBackend` uses the standard
logging module to log debug, warning, and error messages to the logger named
``'django_auth_fogbugz'``. If you need debug messages to help with
configuration issues, you should add a handler to this logger.

.. Note:: This logger works with the `django-debug-toolbar <https://github.com/django-debug-toolbar/django-debug-toolbar>`_ application implicitly.

You can get explicit access to the logger with the following code:

.. code-block:: python

    import logging

    logger = logging.getLogger('django_auth_fogbugz')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.DEBUG)

.. TODO: add example of configuring for the logging section in the django settings file.



.. _settings:

Settings
--------------------------------------


.. _ALLOW_COMMUNITY:

AUTH_FOGBUGZ_ALLOW_COMMUNITY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False``

FogBugz has a concept of 'community' users which do not have full access to the
issue tracker. Instead these users are typically end customers using the site
for technical support. They can see some wiki's and/or discussion databases.

You normally would not want these users to have access to your fogbugz site,
but if you do, set this to ``True``.

If you enable the :ref:`fogbugzprofile` with :ref:`ENABLE_PROFILE`, then the
:py:class:`.django_auth_fogbugz.models.FogBugzProfile` instance for the user
will have the field ``is_community`` set to ``True`` for community users.
This is accessed via ``user.fogbugzprofile.is_community``.




.. _AUTO_CREATE_USERS:

AUTH_FOGBUGZ_AUTO_CREATE_USERS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False`` 

If the user authenticates against the FogBugz server, and there is no django
user, then create one. By default the e-mail address will be used for the
``username``, as FogBugz uses the e-mail address as the user login.

The FogBugz ``sFullname`` will be set as the user model ``first_name``.

If you have :ref:`SERVER_USES_LDAP` enabled, then the user *MUST* login with
their LDAP or Adctive Directory username the first time, when auto-creating
a new user. This is because FogBugz allows for logging in with both the
e-mail address as well as the LDAP username, but the FogBugz API only allows
for retrieving the e-mail address. As such we can discover the e-mail address
from the FogBugz server, but not the LDAP username.

See :ref:`understanding` for more information.


.. _ENABLE_PROFILE:

AUTH_FOGBUGZ_ENABLE_PROFILE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False`` 

Set this to ``True`` to enable the :ref:`fogbugzprofile`. You must also
add ``django_auth_fogbugz`` to your ``INSTALLED_APPS`` setting.

See :ref:`fogbugzpy` and :ref:`fogbugzprofile` for more details.


.. _ENABLE_PROFILE_TOKEN:

AUTH_FOGBUGZ_ENABLE_PROFILE_TOKEN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False``

If set to ``True``, and :ref:`ENABLE_PROFILE` is set to ``True`` then instead
of clearing the FogBugz XML API token after authentication, it will be stored
in the :class:`FogBugzProfile` accessible from the Django User instance as
``user.fogbugzprofile.token``.

.. note:: If you enable token storage, make sure your SESSION_COOKIE_AGE
          is less than or equal to the FogBugz expiration time (2 weeks,
          same as the django default) and that FogBugz Server
          Configuraition for Authentication logon is set to
          ``"Remember Me" Allowed``.

.. warning:: Enabling the profile token extension will allow any code with
             access to the user models to have a login authentication token
             for non-expired users. This could allow Django code to access
             the FogBugz server as those users.

See :ref:`fogbugzpy` and :ref:`fogbugzprofile` for more details.


.. _MAP_ADMIN_AS_STAFF:

AUTH_FOGBUGZ_MAP_ADMIN_AS_STAFF
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False`` 

By setting this to ``True``, FogBugz users whom are assigned as an
"administrator" user, will have their Django user ``is_staff`` field set
to ``True``. This property will sync with each Django login, so if the
FogBugz user is changed to be a "normal" user the ``is_staff`` field will
be set to ``False`` on their next Django login.


.. _MAP_ADMIN_AS_SUPER:

AUTH_FOGBUGZ_MAP_ADMIN_AS_SUPER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False`` 

By setting this to ``True``, FogBugz users whom are assigned as an
"administrator" user, will have their Django user ``is_superuser`` field set
to ``True``. This property will sync with each Django login, so if the
FogBugz user is changed to be a "normal" user the ``is_superuser`` field will
be set to ``False`` on their next Django login.


.. _SERVER:

AUTH_FOGBUGZ_SERVER
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Required: Must be set to a URL, or will error.

**Default:** ``None``

Required root URL to the FogBugz server (e.g. ``https://my_project.fogbugz.com/``).

.. WARNING:: It is strongly recommended that you use an SSL (https) connection
             to perform authentication against th FogBugz server for security.


.. _SERVER_USES_LDAP:

AUTH_FOGBUGZ_SERVER_USES_LDAP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
**Default:** ``False`` 

You *SHOULD* set this to ``True`` if your FogBugz server is configured for LDAP
or Active Directory authentication. When you 

When you hand create user accounts on the Django server, you must use the
LDAP/AD username as the username, and it *MUST* be all lower case. This is
because the FogBugz username matching is case insensitive, but the
Django User model managemnet is not, and the new Django 1.5 ability to
swap out the User model does not allow for case insensitive lookup.

The e-mail address must also be properly set as the FogBugz server allows
for using either the e-mail address or the LDAP/AD username; but it may be
mixed case.

The :py:class:`.django_auth_fogbugz.backend.FogBugzBackend` will lowercase
the username internally.

If :ref:`AUTO_CREATE_USERS` is also set to ``True`` then the first time a new
user logs into Django, they *MUST* use their LDAP/AD username, otherwise the
login will fail. After that they may use either their LDAP/AD username or
their e-mail address.

See :ref:`understanding` for more information.


.. _example:

Settings Template
--------------------------------------

You can copy the sample configuration file and include it in your main
django settings file.

**File:** :file:`django_auth_fogbugz/django_auth_fogbugz_settings.py`

.. literalinclude:: ../django_auth_fogbugz/django_auth_fogbugz_settings.py
   :language: python


Future Work
--------------------------------------

* FogBugz group permissions matching
* Custom hooks for permissions
* Custom hooks for base User model (first_name, last_name, custom User model)
* Custom profile hooking via signals (connect up phone number, gravitar, etc.)
* Multiple FogBugz Servers

License
--------------------------------------

.. include:: ../LICENSE


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

