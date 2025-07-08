from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import Group
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Add user to 'Customer' group by default
            try:
                customer_group = Group.objects.get(name='Customer')
                user.groups.add(customer_group)
            except Group.DoesNotExist:
                # Handle case where group doesn't exist
                pass
            login(request, user)
            return redirect('product_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})