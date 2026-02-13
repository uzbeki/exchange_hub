from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exchange", "0004_luggagelisting_arrival_datetime"),
    ]

    operations = [
        migrations.AddField(
            model_name="luggagelisting",
            name="price_currency",
            field=models.CharField(
                choices=[
                    ("JPY", "Japanese Yen"),
                    ("UZS", "Uzbekistan Sum"),
                    ("USD", "US Dollar"),
                ],
                default="JPY",
                max_length=3,
            ),
        ),
    ]
