from django import forms


class GoogleSignupForm(forms.Form):
    role = forms.ChoiceField(choices=[('student', 'Estudiante'), ('teacher', 'Docente')],
                             widget=forms.Select(attrs={'class': 'form-control'}))
    full_name = forms.CharField(required=False, max_length=150, label='Nombre completo',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}))
    teacher_full_name = forms.CharField(required=False, max_length=150, label='Nombre completo',
                                       widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}))
    specialty = forms.CharField(required=False, max_length=200, label='Especialidad',
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    accept_terms = forms.BooleanField(label='Acepto los términos y condiciones')

    def clean(self):
        data = super().clean()
        teacher = data.get('role') == 'teacher'
        name_field = 'teacher_full_name' if teacher else 'full_name'
        if not data.get(name_field):
            self.add_error(name_field, 'Ingresa tu nombre completo.')
        if teacher and not data.get('specialty'):
            self.add_error('specialty', 'Ingresa tu especialidad.')
        return data
