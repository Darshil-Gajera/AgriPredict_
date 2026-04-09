from django.conf import settings


class AdminSessionMiddleware:
    """
    Gives /admin/ its own session cookie completely separate
    from the main site session. No shared state at all.
    """

    SITE_COOKIE  = 'ap_session'
    ADMIN_COOKIE = 'ap_admin_session'

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_admin = request.path.startswith('/admin/')

        # ── Inject the correct cookie so Django reads the right session ──
        if is_admin:
            # Admin requests read from ADMIN_COOKIE
            request.COOKIES['sessionid'] = request.COOKIES.get(
                self.ADMIN_COOKIE, ''
            )
        else:
            # Normal requests read from SITE_COOKIE
            request.COOKIES['sessionid'] = request.COOKIES.get(
                self.SITE_COOKIE, ''
            )

        response = self.get_response(request)

        # ── After response, rename the set-cookie header ─────────────────
        if 'sessionid' in response.cookies:
            morsel = response.cookies.pop('sessionid')
            target = self.ADMIN_COOKIE if is_admin else self.SITE_COOKIE
            response.cookies[target] = morsel.coded_value
            for attr in ('max-age', 'expires', 'path', 'domain',
                         'secure', 'httponly', 'samesite'):
                val = morsel.get(attr)
                if val:
                    response.cookies[target][attr] = val

        return response