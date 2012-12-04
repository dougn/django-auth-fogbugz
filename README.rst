This authentication backend for django, will authenticate against a
FogBugz (http://www.fogcreek.com/fogbugz/) issue tracker. It uses the
python interface (https://developers.fogbugz.com/default.asp?W199)
to the FogBugz API (http://fogbugz.stackexchange.com/fogbugz-xml-api).

It is HIGHLY recommended that you use an SSL connection to the FogBugz
server for secure authentication.

There is an extension profile model which is included with this auth backend
to help with integrating with the FogBugz API::

    user.fogbugzprofile.token
    user.fogbugzprofile.ixPerson


Example::

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


Settings::

    AUTH_FOGBUGZ_SERVER = "https://my_account.fogbugz.com/"
    
    # By default community users will not be authenticated. If you wish to include
    # FogBugz community user logins, set this to True.
    #
    #AUTH_FOGBUGZ_ALLOW_COMMUNITY = False
    
    # Have django-auth-fogbugz create the django user if it does not already
    # exist, and the user authenticates.
    #
    #AUTH_FOGBUGZ_AUTO_CREATE_USERS = False
    
    # If your FogBugz server is using the LDAP integration for authentication, then
    # You need to set this to True in order to have authentication work properly.
    # If you are also have AUTH_FOGBUGZ_CREATE_NEW_USERS set to True, then the
    # first time a user logs in to the django site, they must use their LDAP
    # username, and not their e-mail address.
    #
    #AUTH_FOGBUGZ_SERVER_USES_LDAP = False
    
    # FogBugz has a concept if a superuser, the 'administrator' flag on accounts.
    # The following settings will map this information to the django account.
    #
    #AUTH_FOGBUGZ_MAP_ADMIN_AS_SUPER = False
    #AUTH_FOGBUGZ_MAP_ADMIN_AS_STAFF = False

    # There is an extension profile model which is included with this auth backend
    # to help with integrating with the FogBugz API::
    #
    #     user.fogbugz.token
    #     user.fogbugz.ixPerson
    #
    # ..warning:: If you enable this profile, make sure your SESSION_COOKIE_AGE
    #             is less than or equal to the FogBugz expiration time (2 weeks,
    #             same as the django default) and that FogBugz Server
    #             Configuraition for Authentication logon is set to
    #            ``"Remember Me" Allowed``.
    #
    # ..warning:: Enabling the user profile extension will allow any code with
    #             access to the user models to have a login authentication token
    #             for non-expired users. This could allow Django code to access
    #             the FogBugz server as those users.
    #
    #AUTH_FOGBUGZ_ENABLE_TOKEN_PROFILE = False
    #SESSION_COOKIE_AGE = 60*60*24*7
    