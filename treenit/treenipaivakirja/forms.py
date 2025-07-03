from django import forms
from treenipaivakirja.models import Harjoitus, Teho, Laji, Tehoalue, Kausi
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm, UserCreationForm, PasswordChangeForm



class HarjoitusForm(forms.ModelForm):
    kesto_h = forms.IntegerField(label='h',min_value=0,required=False,widget=forms.NumberInput({'placeholder': 'h'}))
    kesto_min = forms.IntegerField(label='min',min_value=0,max_value=59,required=False,widget=forms.NumberInput({'placeholder': 'min'}))
    vauhti_min = forms.IntegerField(label='min',min_value=0,required=False,widget=forms.NumberInput({'placeholder': 'min'}))
    vauhti_s = forms.IntegerField(label='s',min_value=0,max_value=59,required=False,widget=forms.NumberInput({'placeholder': 's'}))

    class Meta:
        model = Harjoitus
        widgets = {
            'vuorokaudenaika': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'kommentti': forms.Textarea(attrs={'rows': 3}),
        }
        fields = [
            'pvm',
            'vuorokaudenaika',
            'laji',
            'kesto_h',
            'kesto_min',
            'keskisyke',
            'matka',
            'vauhti_min',
            'vauhti_s',
            'vauhti_km_h',
            'vauhti_min_km',
            'nousu',
            'kalorit',
            'tuntuma',
            'kommentti',
            'reitti',
            'polar_exercise_id'
            ]
    
    def __init__(self, user, *args, **kwargs):
        super(HarjoitusForm, self).__init__(*args, **kwargs)
        for f in self.visible_fields():
            if f.name == 'laji' or f.name == 'tuntuma':
                f.field.widget.attrs['class'] = 'form-select'
            elif f.name != 'vuorokaudenaika' and f.name != 'reitti':
                f.field.widget.attrs['class'] = 'form-control'
        self.fields['laji'].queryset = Laji.objects.filter(user=user)


class LajiForm(forms.ModelForm):
    class Meta:
        model = Laji
        fields = [
            'laji',
            'laji_nimi',
            'laji_ryhma'
            ]
        widgets = {
            'laji': forms.TextInput(attrs={'class': 'form-control'}),
            'laji_nimi': forms.TextInput(attrs={'class': 'form-control'}),
            'laji_ryhma': forms.TextInput(attrs={'class': 'form-control'})
        }


class TehoForm(forms.ModelForm):
    nro = forms.IntegerField(min_value=0)
    kesto_h = forms.IntegerField(label='Kesto (h)',min_value=0,required=False,widget=forms.NumberInput({'placeholder': 'h'}))
    kesto_min = forms.IntegerField(label='Kesto (min)',min_value=0,max_value=59,required=False,widget=forms.NumberInput({'placeholder': 'min'}))
    vauhti_min = forms.IntegerField(label='Vauhti (min)',min_value=0,required=False,widget=forms.NumberInput({'placeholder': 'min'}))
    vauhti_s = forms.IntegerField(label='Vauhti (s)',min_value=0,max_value=59,required=False,widget=forms.NumberInput({'placeholder': 's'}))

    class Meta:
        model = Teho
        fields = [
            'nro',
            'tehoalue',
            'kesto_h',
            'kesto_min',
            'kesto',
            'keskisyke',
            'maksimisyke',
            'matka',
            'vauhti_min',
            'vauhti_s',
            'vauhti_min_km',
            'vauhti_km_h'
            ]

        
    def __init__(self, *args, **kwargs):
        super(TehoForm, self).__init__(*args, **kwargs)
        for f in self.visible_fields():
            if f.name == 'tehoalue':
                f.field.widget.attrs['class'] = 'form-select'
            else:
                f.field.widget.attrs['class'] = 'form-control'


class TehoalueForm(forms.ModelForm):
    class Meta:
        model = Tehoalue
        fields = [
            'jarj_nro',
            'tehoalue',
            'alaraja',
            'ylaraja'
            ]
        widgets = {
            'jarj_nro': forms.NumberInput(attrs={'class': 'form-control'}),
            'tehoalue': forms.TextInput(attrs={'class': 'form-control'}),
            'alaraja': forms.NumberInput(attrs={'class': 'form-control'}),
            'ylaraja': forms.NumberInput(attrs={'class': 'form-control'})
        }


class UserForm(UserChangeForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name', 
            'email', 
            'password'
            ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control'})
        }


class PwChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(PwChangeForm, self).__init__(*args, **kwargs)
        for f in self.visible_fields():
            f.field.widget.attrs['class'] = 'form-control'


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(required=False, label='Etunimi')
    last_name = forms.CharField(required=False, label='Sukunimi')
    email = forms.EmailField(required=False, label='Sähköposti')

    class Meta:
        model = User
        fields = [
            'username', 
            'first_name', 
            'last_name', 
            'email', 
            'password1', 
            'password2'
            ]
        
    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        for f in self.visible_fields():
            f.field.widget.attrs['class'] = 'form-control'


class KausiForm(forms.ModelForm):
    class Meta:
        model = Kausi
        fields = [
            'kausi',
            'alkupvm',
            'loppupvm'
            ]
        widgets = {
            'kausi': forms.TextInput(attrs={'class': 'form-control'}),
            'alkupvm': forms.DateInput(attrs={'class': 'form-control date-picker picker-start'}),
            'loppupvm': forms.DateInput(attrs={'class': 'form-control date-picker picker-end'})
        }

    def clean(self):
        cleaned_data = super().clean()
        alkupvm = cleaned_data.get("alkupvm")
        loppupvm = cleaned_data.get("loppupvm")

        if alkupvm and loppupvm:
            if loppupvm < alkupvm:
                raise forms.ValidationError("Loppupäivä ei voi olla pienempi kuin alkupäivä.")


class HarjoitusFormSet(forms.BaseFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields['polar_sport'] = forms.CharField(widget=forms.TextInput(attrs={
            'class': 'form-control-plaintext text-muted',
            'readonly':True
            }))
        form.fields['has_route'] = forms.BooleanField(
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            label='Tallenna reitti',
            required=False
            )