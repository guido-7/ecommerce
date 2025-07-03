from django import forms
from .models import Category, Product, ProductImage

class CategoryForm(forms.ModelForm):
    """
    Form for creating and updating a Category.
    The slug is handled automatically in the view.
    """
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Es. T-shirt, Tazze, Accessori'}),
        }
        labels = {
            'name': 'Nome Categoria',
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
                raise forms.ValidationError("Una categoria con questo nome esiste già.")
        # On create
        elif Category.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError("Una categoria con questo nome esiste già.")
        return name