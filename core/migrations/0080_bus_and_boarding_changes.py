# Generated manually to align DB with model changes: Bus, BoardingPoint timing/fee, Driver->bus, BusApplication->bus
from django.db import migrations, models
import django.db.models.deletion


def create_buses_and_move_data(apps, schema_editor):
    BusRoute = apps.get_model('core', 'BusRoute')
    Bus = apps.get_model('core', 'Bus')
    BoardingPoint = apps.get_model('core', 'BoardingPoint')
    Driver = apps.get_model('core', 'Driver')
    BusApplication = apps.get_model('core', 'BusApplication')

    db_alias = schema_editor.connection.alias
    for route in BusRoute.objects.using(db_alias).all():
        # route may have had bus_no and total_seat fields previously
        bus_no = getattr(route, 'bus_no', None)
        total_seat = getattr(route, 'total_seat', None)
        if bus_no is None:
            bus_no = f"BUS-{route.id}"
        if total_seat is None:
            total_seat = 0
        bus = Bus.objects.using(db_alias).create(route_id=route.id, bus_no=bus_no, total_seat=total_seat)
        # Move boarding points that referenced route -> now reference this new bus
        BoardingPoint.objects.using(db_alias).filter(route_id=route.id).update(bus_id=bus.id)
        # Move drivers referencing route -> set to this bus
        Driver.objects.using(db_alias).filter(route_id=route.id).update(bus_id=bus.id)
        # Move existing applications referencing route -> set bus to this bus
        BusApplication.objects.using(db_alias).filter(route_id=route.id).update(bus_id=bus.id)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0079_transportation'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bus_no', models.CharField(max_length=20)),
                ('total_seat', models.PositiveIntegerField()),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buses', to='core.busroute')),
            ],
        ),
        migrations.AddField(
            model_name='boardingpoint',
            name='bus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='boarding_points', to='core.bus'),
        ),
        migrations.AddField(
            model_name='boardingpoint',
            name='timing',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='boardingpoint',
            name='fee',
            field=models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='driver',
            name='bus',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='driver', to='core.bus'),
        ),
        migrations.AddField(
            model_name='busapplication',
            name='bus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.bus'),
        ),
        migrations.RunPython(create_buses_and_move_data, reverse_code=migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='boardingpoint',
            name='route',
        ),
        migrations.RemoveField(
            model_name='driver',
            name='route',
        ),
        migrations.RemoveField(
            model_name='busroute',
            name='bus_no',
        ),
        migrations.RemoveField(
            model_name='busroute',
            name='total_seat',
        ),
        # Make new fields non-nullable now that data has been migrated
        migrations.AlterField(
            model_name='boardingpoint',
            name='bus',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='boarding_points', to='core.bus'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='bus',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='driver', to='core.bus'),
        ),
        migrations.AlterField(
            model_name='busapplication',
            name='bus',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.bus'),
        ),
    ]
