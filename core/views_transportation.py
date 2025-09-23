from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BusApplicationForm
from .transport_models import BusRoute, BusApplication, Bus


def staff_transportation(request):
    # Load routes with buses and their boarding points
    routes = BusRoute.objects.all().prefetch_related('buses__boarding_points', 'buses__driver')

    if request.method == 'POST':
        form = BusApplicationForm(request.POST)
        if form.is_valid():
            # Use the selected bus to check seats (routes no longer have total_seat)
            bus = form.cleaned_data.get('bus')
            if not bus:
                messages.error(request, 'Please select a bus.')
            else:
                already_applied = BusApplication.objects.filter(bus=bus).count()
                available = max(0, bus.total_seat - already_applied)
                if available <= 0:
                    messages.error(request, 'No seats available on the selected bus.')
                else:
                    # Ensure route matches bus (defensive) and save
                    route = form.cleaned_data.get('route')
                    if route and bus.route_id != route.id:
                        form.add_error('bus', 'Selected bus does not belong to the chosen route.')
                    else:
                        form.save()
                        messages.success(request, 'Application submitted successfully!')
                        return redirect('staff_transportation')
    else:
        form = BusApplicationForm()

    # Add a small helper to compute available seats per route and include boarding point details
    route_list = []
    for r in routes:
        buses_data = []
        for b in r.buses.all():
            applied = BusApplication.objects.filter(bus=b).count()
            available_seats = max(0, b.total_seat - applied)
            bps = []
            for bp in b.boarding_points.all():
                bps.append({
                    'id': bp.id,
                    'name': getattr(bp, 'name', ''),
                    'timing': getattr(bp, 'timing', '') if hasattr(bp, 'timing') else '',
                    'fee': str(getattr(bp, 'fee', '')) if hasattr(bp, 'fee') else '',
                })
            buses_data.append({
                'id': b.id,
                'bus_no': b.bus_no,
                'total_seat': b.total_seat,
                'available_seats': available_seats,
                'driver': getattr(getattr(b, 'driver', None), 'name', ''),
                'mobile': getattr(getattr(b, 'driver', None), 'number', ''),
                'boarding_points': bps,
            })
        route_list.append({
            'id': r.id,
            'name': r.name,
            'buses': buses_data,
        })

    return render(request, 'staff_transportation.html', {'routes': routes, 'form': form, 'route_list': route_list})


def transportation_page(request):
    routes = BusRoute.objects.all().prefetch_related('buses__boarding_points', 'buses__driver')
    if request.method == 'POST':
        form = BusApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application submitted successfully!')
            return redirect('transportation')
    else:
        form = BusApplicationForm()

    route_list = []
    for r in routes:
        buses_data = []
        for b in r.buses.all():
            applied = BusApplication.objects.filter(bus=b).count()
            available_seats = max(0, b.total_seat - applied)
            bps = []
            for bp in b.boarding_points.all():
                bps.append({
                    'point': bp.name,
                    'timings': getattr(bp, 'timing', '') or '',
                    'bus_no': b.bus_no,
                })
            buses_data.append({'id': b.id, 'bus_no': b.bus_no, 'available_seats': available_seats, 'boarding_points': bps})
        route_list.append({'id': r.id, 'name': r.name, 'buses': buses_data})

    return render(request, 'transportation.html', {'routes': routes, 'form': form, 'route_list': route_list})
