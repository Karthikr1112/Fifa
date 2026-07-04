from django import forms
from .models import Customer, Gift


class CustomerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'mobile_number', 'aadhar_number', 'bill_number', 'game_result', 'won_gift']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Enter full name',
                'autofocus': True,
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '10-digit mobile number',
                'maxlength': '10',
                'pattern': '[0-9]{10}',
                'inputmode': 'numeric',
            }),
            'aadhar_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '12-digit Aadhar number',
                'maxlength': '12',
                'pattern': '[0-9]{12}',
                'inputmode': 'numeric',
            }),
            'bill_number': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Bill / Invoice number',
            }),
            'game_result': forms.Select(attrs={'class': 'form-select form-select-lg'}),
            'won_gift': forms.Select(attrs={'class': 'form-select form-select-lg'}),
        }
        labels = {
            'name': 'Customer Name',
            'mobile_number': 'Mobile Number',
            'aadhar_number': 'Aadhar Number',
            'bill_number': 'Bill Number',
            'game_result': 'Game Result',
            'won_gift': 'Gift',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['game_result'].required = False
        self.fields['won_gift'].required = False
        self.fields['won_gift'].queryset = Gift.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        game_result = cleaned_data.get('game_result')
        won_gift = cleaned_data.get('won_gift')
        if game_result == Customer.RESULT_WIN and not won_gift:
            self.add_error('won_gift', 'Please select a gift for a winning customer.')
        if game_result != Customer.RESULT_WIN:
            cleaned_data['won_gift'] = None
        return cleaned_data

    def clean_mobile_number(self):
        mobile = self.cleaned_data.get('mobile_number', '').strip()
        if not mobile.isdigit() or len(mobile) != 10:
            raise forms.ValidationError('Mobile number must be exactly 10 digits.')
        if Customer.objects.filter(mobile_number=mobile).exists():
            raise forms.ValidationError(
                'This mobile number is already registered. Each customer can play only once.'
            )
        return mobile

    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number', '').strip()
        if not aadhar.isdigit() or len(aadhar) != 12:
            raise forms.ValidationError('Aadhar number must be exactly 12 digits.')
        if Customer.objects.filter(aadhar_number=aadhar).exists():
            raise forms.ValidationError(
                'This Aadhar number is already registered. Each customer can play only once.'
            )
        return aadhar

    def clean_bill_number(self):
        bill = self.cleaned_data.get('bill_number', '').strip().upper()
        if Customer.objects.filter(bill_number=bill).exists():
            raise forms.ValidationError(
                'This bill number is already used. Each bill can be used only once.'
            )
        return bill

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError('Please enter a valid name (at least 2 characters).')
        return name


from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        required=True
    )
    role = forms.ChoiceField(
        choices=[('staff', 'Entry Staff'), ('admin', 'Administrator')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Role"
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # When editing, password is not required
            self.fields['password'].required = False
            self.fields['password'].help_text = "Leave blank if you don't want to change the password."
            # Set initial role
            if self.instance.is_staff:
                self.initial['role'] = 'admin'
            else:
                self.initial['role'] = 'staff'

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
            
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
            
        if commit:
            user.save()
        return user
