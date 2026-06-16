from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("rentals", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("paid", "Paid"),
                            ("expired", "Expired"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("rental", "Rental"),
                            ("cancellation_fee", "Cancellation_fee"),
                            ("overdue_fee", "Overdue_fee"),
                        ],
                        default="rental",
                        max_length=20,
                    ),
                ),
                ("session_url", models.URLField(blank=True, null=True)),
                (
                    "session_id",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "money_to_pay",
                    models.DecimalField(decimal_places=2, max_digits=10),
                ),
                (
                    "rental",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="payments",
                        to="rentals.rental",
                    ),
                ),
            ],
        ),
    ]
