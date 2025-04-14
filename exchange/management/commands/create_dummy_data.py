# exchange/management/commands/create_dummy_data.py

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # Keep this if used elsewhere

from faker import Faker  # Import Faker

# Import your models
from exchange.models import Request, Conversation, Message

# Get the User model configured in settings
User = get_user_model()


class Command(BaseCommand):
    help = """Creates dummy data for the application, including users, requests, 
    conversations, and messages. This command is useful for testing and 
    development purposes. You can customize the number of each type of data 
    to be created using the following arguments:

    Arguments:
      --users: Number of dummy users to create (default: 50).
      --requests: Number of dummy requests to create (default: 200).
      --conversations: Approximate number of dummy conversations to create (default: 300).
      --messages: Approximate number of dummy messages to create (default: 2000).
      --password: Default password for dummy users (default: '6p2VLY94O53sgDfZwo0HbvCUmiJWhSAzXdj').
    """

    # Add command-line arguments for customization
    def add_arguments(self, parser):
        parser.add_argument(
            "--users", type=int, default=50, help="Number of dummy users to create."
        )
        parser.add_argument(
            "--requests",
            type=int,
            default=200,
            help="Number of dummy requests to create. Default: 200.",
        )
        parser.add_argument(
            "--conversations",
            type=int,
            default=300,
            help="Approximate number of dummy conversations to create. Default: 300.",
        )
        parser.add_argument(
            "--messages",
            type=int,
            default=2000,
            help="Approximate number of dummy messages to create. Default: 2000.",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="6p2VLY94O53sgDfZwo0HbvCUmiJWhSAzXdj",
            help="Default password for dummy users. Default: '6p2VLY94O53sgDfZwo0HbvCUmiJWhSAzXdj'.",
        )

    @transaction.atomic  # Wrap in a transaction for efficiency and atomicity
    def handle(self, *args, **options):
        num_users = options["users"]
        num_requests = options["requests"]
        num_conversations = options["conversations"]
        num_messages = options["messages"]
        default_password = options["password"]

        fake = Faker()  # Initialize Faker

        self.stdout.write(self.style.SUCCESS("Starting dummy data creation..."))

        # === 1. Create Users ===
        self.stdout.write(f"Creating {num_users} users...")
        users = []
        for i in range(num_users):
            # username = f"testuser_{i+1}"
            username = fake.user_name()  # Generate a random username
            email = fake.email()
            try:
                user = User.objects.create_user(
                    username=username, email=email, password=default_password
                )
                # Add other user profile fields if you have them
                # user.profile.full_name = fake.name()
                # user.profile.save()
                users.append(user)
                if (i + 1) % 10 == 0:
                    self.stdout.write(f"...created {i+1}/{num_users} users.")
            except IntegrityError:
                self.stdout.write(
                    self.style.WARNING(
                        f"User {username} likely already exists, skipping."
                    )
                )
                # Try to fetch the existing user if needed for subsequent steps
                try:
                    users.append(User.objects.get(username=username))
                except User.DoesNotExist:
                    pass  # Should not happen if IntegrityError was due to username

        if not users:
            self.stdout.write(
                self.style.ERROR(
                    "No users available. Cannot create requests/conversations."
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f"Successfully created/found {len(users)} users.")
        )

        # === 2. Create Requests ===
        self.stdout.write(f"Creating {num_requests} requests...")
        requests = []
        active_requests = []  # Keep track of active ones for conversations
        type_choices = [choice[0] for choice in Request.TYPE_CHOICES]
        currency_choices = [choice[0] for choice in Request.CURRENCY_CHOICES]
        status_choices = [choice[0] for choice in Request.STATUS_CHOICES]

        for i in range(num_requests):
            request_user = random.choice(users)
            req_type = random.choice(type_choices)
            currency = random.choice(currency_choices)
            amount = Decimal(random.randint(1000, 1000000))
            deadline = timezone.now() + timedelta(
                days=random.randint(1, 90), hours=random.randint(1, 23)
            )
            # Make ~20% completed, the rest active
            status = "completed" if random.random() < 0.2 else "active"
            urgent = random.choice([True, False])
            hide_contacts = random.choice([True, False])
            conditions = (
                fake.sentence() if random.random() < 0.5 else ""
            )  # ~50% have conditions

            req = Request.objects.create(
                user=request_user,
                type=req_type,
                amount=amount,
                currency=currency,
                deadline=deadline,
                urgent=urgent,
                conditions=conditions,
                status=status,
                hide_contacts=hide_contacts,
            )
            requests.append(req)
            if status == "active":
                active_requests.append(req)

            if (i + 1) % 20 == 0:
                self.stdout.write(f"...created {i+1}/{num_requests} requests.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully created {len(requests)} requests ({len(active_requests)} active)."
            )
        )

        if not active_requests:
            self.stdout.write(
                self.style.WARNING(
                    "No active requests created. Cannot create conversations."
                )
            )
            # Continue to message creation if needed, though they won't make sense
        else:
            # === 3. Create Conversations ===
            self.stdout.write(
                f"Attempting to create up to {num_conversations} conversations..."
            )
            conversations = []
            attempts = 0
            max_attempts = (
                num_conversations * 3
            )  # Allow for failures due to user collision/existing

            while len(conversations) < num_conversations and attempts < max_attempts:
                attempts += 1
                request_obj = random.choice(active_requests)
                request_owner = request_obj.user
                possible_participants = [u for u in users if u != request_owner]

                if not possible_participants:
                    continue  # Skip if only one user exists

                other_participant = random.choice(possible_participants)

                # Ensure consistent participant order for unique_together
                p1 = min(request_owner, other_participant, key=lambda u: u.pk)
                p2 = max(request_owner, other_participant, key=lambda u: u.pk)

                try:
                    # Use get_or_create to handle potential duplicates gracefully
                    conversation, created = Conversation.objects.get_or_create(
                        request=request_obj,
                        participant1=p1,
                        participant2=p2,
                    )
                    if created:
                        conversations.append(conversation)
                        if len(conversations) % 25 == 0:
                            self.stdout.write(
                                f"...created {len(conversations)}/{num_conversations} conversations."
                            )

                except IntegrityError:
                    # This might happen with race conditions if not using get_or_create,
                    # but get_or_create should handle it. Log just in case.
                    self.stdout.write(
                        self.style.WARNING(
                            "Integrity error during conversation creation (should be rare with get_or_create)."
                        )
                    )
                    pass

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created {len(conversations)} conversations."
                )
            )

            # === 4. Create Messages ===
            # Fetch all conversations created or found previously
            all_conversations = list(Conversation.objects.filter(request__in=requests))

            if not all_conversations:
                self.stdout.write(
                    self.style.WARNING(
                        "No conversations available to create messages for."
                    )
                )
            else:
                self.stdout.write(f"Creating {num_messages} messages...")
                messages_created_count = 0
                for i in range(num_messages):
                    conversation_obj = random.choice(all_conversations)
                    sender = random.choice(
                        [conversation_obj.participant1, conversation_obj.participant2]
                    )
                    content = fake.sentence(nb_words=random.randint(5, 25))
                    # Simulate read status - maybe older messages are more likely read
                    # For simplicity, let's just make ~70% read
                    is_read = random.random() < 0.7

                    # Create message (auto_now_add handles timestamp)
                    Message.objects.create(
                        conversation=conversation_obj,
                        sender=sender,
                        content=content,
                        is_read=is_read,
                    )
                    messages_created_count += 1

                    if (i + 1) % 100 == 0:
                        self.stdout.write(f"...created {i+1}/{num_messages} messages.")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully created {messages_created_count} messages."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Dummy data creation complete!"))
