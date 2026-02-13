from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exchange", "0003_luggage_telegram_subscription_and_link_token"),
    ]

    operations = [
        migrations.AddField(
            model_name="luggagelisting",
            name="arrival_datetime",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
