from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BusApplicationForm
from .transport_models import BusRoute, BusApplication

def transportation_page(request):
    routes = BusRoute.objects.all().prefetch_related('boarding_points')
    if request.method == 'POST':
        form = BusApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('transportation')
    else:
        form = BusApplicationForm()
    return render(request, 'transportation.html', {'routes': routes, 'form': form})
