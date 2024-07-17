from rest_framework_simplejwt.tokens import RefreshToken

class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user):
        token = cls()
        token['username'] = str(user.username)
        return token
