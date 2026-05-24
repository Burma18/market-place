from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def migrate_completed_to_paid(apps, schema_editor):
    Order = apps.get_model('products', 'Order')
    Order.objects.filter(status='completed').update(status='paid')


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Ожидает оплаты'),
                    ('paid', 'Оплачен'),
                    ('cancelled', 'Отменён'),
                    ('failed', 'Ошибка'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='stripe_session_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.RunPython(migrate_completed_to_paid, migrations.RunPython.noop),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='products.order')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='products.product')),
            ],
            options={
                'verbose_name': 'Позиция заказа',
                'verbose_name_plural': 'Позиции заказа',
            },
        ),
    ]
