===================================================================
django-auth-fogbugz - Django FogBugz Authentication Backend
===================================================================

This authentication backend for django, will authenticate against a
FogBugz (http://www.fogcreek.com/fogbugz/) issue tracker. It uses the
python interface (https://developers.fogbugz.com/default.asp?W199)
to the FogBugz API (http://fogbugz.stackexchange.com/fogbugz-xml-api).

.. warning::
   It is HIGHLY recommended that you use an SSL connection to the FogBugz
   server for secure authentication.

User Model Extension
-----------------------------
There is an extension profile model which is included with this auth backend
to help with integrating with the FogBugz API when you set
``AUTH_FOGBUGZ_ENABLE_PROFILE`` to ``True`` in your settings, and include
``django-auth-fogbugz`` as an application in INSTALLED_APPS (see below)::

    user.fogbugzprofile.token
    user.fogbugzprofile.ixPerson
    user.fogbugzprofile.is_normal
    user.fogbugzprofile.is_community
    user.fogbugzprofile.is_administrator


Example:

.. code:: python

    import fogbugz
    from django.conf import settings

    fb = fogbugz.FogBugz(settings.AUTH_FOGBUGZ_SERVER,
                         user.fogbugzprofile.token)
    resp = fb.search(q='assignedTo:"me" status:"Active"',
                    cols="ixBug,sTitle",
                    max=10)
    top_ten = ''
    for case in resp.cases.findAll('case'):
         top_ten += "%s: %s\n" % (case.ixbug.string, 
                                  case.stitle.string.encode('UTF-8'))


Settings
--------

.. code:: python


    AUTH_FOGBUGZ_SERVER = "https://my_account.fogbugz.com/"
    
    # By default community users will not be authenticated. If you wish to include
    # FogBugz community user logins, set this to True.
    #
    AUTH_FOGBUGZ_ALLOW_COMMUNITY = False
    
    # Have django-auth-fogbugz create the django user if it does not already
    # exist, and the user authenticates.
    #
    AUTH_FOGBUGZ_AUTO_CREATE_USERS = False
    
    # If your FogBugz server is using the LDAP integration for authentication, then
    # You need to set this to True in order to have authentication work properly.
    # If you are also have AUTH_FOGBUGZ_AUTO_CREATE_USERS set to True, then the
    # first time a user logs in to the django site, they must use their LDAP
    # username, and not their e-mail address.
    #
    AUTH_FOGBUGZ_SERVER_USES_LDAP = False
    
    # FogBugz has a concept if a superuser, the 'administrator' flag on accounts.
    # The following settings will map this information to the django account.
    #
    AUTH_FOGBUGZ_MAP_ADMIN_AS_SUPER = False
    AUTH_FOGBUGZ_MAP_ADMIN_AS_STAFF = False

    # There is an extension profile model which is included with this auth backend
    # to help with integrating with the FogBugz API::
    #
    #     user.fogbugzprofile.ixPerson
    #     user.fogbugzprofile.is_community
    #     user.fogbugzprofile.is_administrator
    #
    #
    # You must also add 'django-auth-fogbugz' as django app in your
    # INSTALLED_APPS when enabling this.
    #
    AUTH_FOGBUGZ_ENABLE_PROFILE = False

    # With the fogbugz profile extension enabled, there is the option to store
    # the serurity login token for the FogBugz user. This token can be used
    # instead of the username and password to log into the FogBugz server.
    # The authentication token can be accessed via the profile::
    #
    #     user.fogbugzprofile.token
    #
    #
    # ..note:: If you enable token storage, make sure your SESSION_COOKIE_AGE
    #          is less than or equal to the FogBugz expiration time (2 weeks,
    #          same as the django default) and that FogBugz Server
    #          Configuraition for Authentication logon is set to
    #          ``"Remember Me" Allowed``.
    #
    # ..warning:: Enabling the profile token extension will allow any code with
    #             access to the user models to have a login authentication token
    #             for non-expired users. This could allow Django code to access
    #             the FogBugz server as those users.
    #
    # You must also add 'django-auth-fogbugz' as django app in your
    # INSTALLED_APPS and set AUTH_FOGBUGZ_ENABLE_PROFILE to true
    # when enabling this.
    #
    AUTH_FOGBUGZ_ENABLE_PROFILE_TOKEN = False
    
    # Keep ModelBackend around for per-user permissions and maybe a local
    # superuser.
    AUTHENTICATION_BACKENDS = (
        'django_auth_fogbugz.backend.FogBugzBackend',
        'django.contrib.auth.backends.ModelBackend',
    )
    