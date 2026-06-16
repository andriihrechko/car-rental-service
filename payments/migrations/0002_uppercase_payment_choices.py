from django.db import migrations, models


def uppercase_payment_choices(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")
    status_values = {
        "pending": "PENDING",
        "paid": "PAID",
        "expired": "EXPIRED",
    }
    type_values = {
        "rental": "RENTAL",
        "cancellation_fee": "CANCELLATION_FEE",
        "overdue_fee": "OVERDUE_FEE",
    }

    for old_value, new_value in status_values.items():
        Payment.objects.filter(status=old_value).update(status=new_value)

    for old_value, new_value in type_values.items():
        Payment.objects.filter(type=old_value).update(type=new_value)


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            uppercase_payment_choices,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="payment",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("PAID", "Paid"),
                    ("EXPIRED", "Expired"),
                ],
                default="PENDING",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="type",
            field=models.CharField(
                choices=[
                    ("RENTAL", "Rental"),
                    ("CANCELLATION_FEE", "Cancellation fee"),
                    ("OVERDUE_FEE", "Overdue fee"),
                ],
                default="RENTAL",
                max_length=20,
            ),
        ),
    ]
