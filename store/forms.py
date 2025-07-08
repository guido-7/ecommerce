from django import forms
from .models import Category, Brand

class CategoryForm(forms.ModelForm):
    """
    Form for creating and updating a Category.
    The slug is handled automatically in the view.
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. TV, Phone, PC'}),
        }
        labels = {
            'name': 'Name Category',
        }

    def clean_name(self):
        """
        Ensures the category name is unique (case-insensitive).
        """
        name = self.cleaned_data.get('name')
        # On update, exclude the current instance from the check
        instance = self.instance
        if instance and instance.pk:
            if Category.objects.filter(name__iexact=name).exclude(pk=instance.pk).exists():
                raise forms.ValidationError("A category with this name already exists.")
        # On create
        elif Category.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name


class BrandForm(forms.ModelForm):
    """
        Form for creating and updating a Brand.
        The slug is handled automatically in the view.
    """
    class Meta:
        model = Brand
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. Apple, Samsung, Dell'}),
        }
        labels = {
            'name': 'Name Brand',
        }

    def clean_name(self):
        """
        Ensures the brand name is unique (case-insensitive).
        """
        name = self.cleaned_data.get('name')
        # On update, exclude the current instance from the check
        instance = self.instance
        if instance and instance.pk:
            if Brand.objects.filter(name__iexact=name).exclude(pk=instance.pk).exists():
                raise forms.ValidationError("A brand with this name already exists.")
        # On create
        elif Category.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("A brand with this name already exists.")
        return name


class PromoCodeForm(forms.Form):
    code = forms.CharField(
        label="Promo Code",
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter the promo code',
                'class': 'form-control'
            }
        )
    )