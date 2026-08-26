from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from captcha.fields import CaptchaField
import re

User = get_user_model()

ROLES_CHOICES = (
    ('student', 'Estudiante'),
    ('teacher', 'Docente'),
)

class RegisterForm(UserCreationForm):
    # Datos básicos
    username = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Elige un nombre de usuario',
        'minlength': '3'
    }))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'ejemplo@correo.com'
    }))
    password1 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Mínimo 8 caracteres'
    }))
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Confirma tu contraseña'
    }))
    
    # Rol
    role = forms.ChoiceField(choices=ROLES_CHOICES, required=True, widget=forms.Select(attrs={
        'class': 'form-control',
        'id': 'id_role'
    }))
    
    # Campos para estudiante
    full_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Tu nombre completo'
    }))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ej: 79123456'
    }))
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Tu ciudad'
    }))
    education_level = forms.ChoiceField(required=False, choices=(
        ('', 'Selecciona tu nivel de estudios'),
        ('secundaria', 'Secundaria'),
        ('tecnico', 'Técnico Superior'),
        ('universitario', 'Universitario'),
        ('posgrado', 'Posgrado/Maestría'),
        ('doctorado', 'Doctorado'),
    ), widget=forms.Select(attrs={'class': 'form-control'}))
    university = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Nombre de tu universidad o institución'
    }))
    career = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Carrera que estudias'
    }))
    semester = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Semestre/año en curso'
    }))
    interests = forms.MultipleChoiceField(required=False, choices=(
        ('programacion', 'Programación'),
        ('diseno', 'Diseño'),
        ('marketing', 'Marketing Digital'),
        ('negocios', 'Negocios'),
        ('idiomas', 'Idiomas'),
        ('ciencia', 'Ciencia'),
        ('arte', 'Arte'),
        ('musica', 'Música'),
        ('deportes', 'Deportes'),
        ('fotografia', 'Fotografía'),
    ), widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    
    # Campos para docente
    teacher_full_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Tu nombre completo'
    }))
    teacher_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Ej: 79123456'
    }))
    teacher_email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'email@institucion.com'
    }))
    specialty = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Tu especialidad o área de expertise'
    }))
    experience_years = forms.ChoiceField(required=False, choices=(
        ('', 'Años de experiencia'),
        ('0-1', 'Menos de 1 año'),
        ('1-3', '1-3 años'),
        ('3-5', '3-5 años'),
        ('5-10', '5-10 años'),
        ('10+', 'Más de 10 años'),
    ), widget=forms.Select(attrs={'class': 'form-control'}))
    teaching_materials = forms.MultipleChoiceField(required=False, choices=(
        ('videos', 'Videos HD'),
        ('documentos', 'Documentos/PDF'),
        ('presentaciones', 'Presentaciones'),
        ('ejercicios', 'Ejercicios prácticos'),
        ('proyectos', 'Proyectos reales'),
        ('examenes', 'Exámenes'),
        ('certificados', 'Certificados'),
    ), widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    teaching_level = forms.MultipleChoiceField(required=False, choices=(
        ('principiante', 'Principiante'),
        ('intermedio', 'Intermedio'),
        ('avanzado', 'Avanzado'),
        ('experto', 'Experto'),
    ), widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}))
    institution = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Institución donde enseñas'
    }))
    teacher_bio = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': '3',
        'placeholder': 'Cuéntanos sobre tu experiencia como docente...'
    }))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://linkedin.com/in/tu-perfil'
    }))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://tu-sitio-web.com'
    }))
    
    # CAPTCHA
    captcha = CaptchaField(label='Código de seguridad')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            if field_name not in ['username', 'email', 'password1', 'password2', 'role', 'captcha']:
                self.fields[field_name].required = False

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nombre de usuario ya está registrado')
        if len(username) < 3:
            raise ValidationError('El nombre de usuario debe tener al menos 3 caracteres')
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError('Solo letras, números y guión bajo')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado')
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('Debe tener al menos una mayúscula')
        if not re.search(r'[a-z]', password):
            raise ValidationError('Debe tener al menos una minúscula')
        if not re.search(r'[0-9]', password):
            raise ValidationError('Debe tener al menos un número')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('Debe tener al menos un carácter especial (!@#$%^&*)')
        return password

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'student':
            if not cleaned_data.get('full_name'):
                self.add_error('full_name', 'El nombre completo es requerido para estudiantes')
            if not cleaned_data.get('university'):
                self.add_error('university', 'La universidad/institución es requerida')
            if not cleaned_data.get('career'):
                self.add_error('career', 'La carrera es requerida')
                
        elif role == 'teacher':
            if not cleaned_data.get('teacher_full_name'):
                self.add_error('teacher_full_name', 'El nombre completo es requerido para docentes')
            if not cleaned_data.get('specialty'):
                self.add_error('specialty', 'La especialidad es requerida')
            if not cleaned_data.get('experience_years'):
                self.add_error('experience_years', 'Los años de experiencia son requeridos')
                
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        
        if self.cleaned_data.get('phone'):
            user.phone = self.cleaned_data.get('phone')
        elif self.cleaned_data.get('teacher_phone'):
            user.phone = self.cleaned_data.get('teacher_phone')
            
        if self.cleaned_data.get('full_name'):
            user.first_name = self.cleaned_data.get('full_name')
        elif self.cleaned_data.get('teacher_full_name'):
            user.first_name = self.cleaned_data.get('teacher_full_name')
            
        if commit:
            user.save()
        return user


# ============================================
# LOGIN FORM CON CAPTCHA
# ============================================
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Usuario o email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Contraseña'
    }))
    captcha = CaptchaField(label='Código de seguridad')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'bio', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 79123456'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Cuéntanos sobre ti...'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }