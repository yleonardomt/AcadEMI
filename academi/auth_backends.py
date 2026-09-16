from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """El campo de login ya dice "Usuario o email" (LoginForm), pero el
    ModelBackend por defecto de Django solo compara contra username. Este
    backend resuelve el valor ingresado contra username O email antes de
    verificar la contraseña, para que esa promesa sea real — necesario
    además porque el registro ya no pide un username manual."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).order_by('id').first()

        # A propósito NO se filtra aquí por user_can_authenticate() (que
        # rechaza is_active=False): si lo hiciéramos, authenticate()
        # devolvería None para una cuenta desactivada exactamente igual
        # que para una contraseña incorrecta, y LoginForm.confirm_login_allowed
        # (heredado de AuthenticationForm) nunca llegaría a ejecutarse para
        # mostrar el mensaje específico de "cuenta desactivada" — se vería
        # el genérico de "usuario o contraseña incorrectos" en ambos casos.
        if user.check_password(password):
            return user
        return None
