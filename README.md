# Open Exchange Hub

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2-green)](https://www.djangoproject.com/)

🌍 **Open Exchange Hub** is a peer-to-peer platform designed to connect Uzbek expats and others who need to exchange currencies (e.g., 💴 JPY, 🇺🇿 UZS, 💵 USD) between Uzbekistan and other countries. The platform facilitates direct connections, allowing users to bypass traditional bank fees and transfer service commissions.

Today the platform includes two connected flows:

- 💱 **Money Exchange Hub**: Post send/receive offers, find matches, and chat directly.
- 🧳 **Luggage Space Marketplace**: Travelers post available kg, buyers reserve space, and sellers manage reservations.

## ✨ Features

- 💱 **Money Offer Posting**: Create send/receive offers with amount, currency, deadline, urgency, and conditions.
- 💬 **Secure Conversations**: Start direct conversations from offers and manage unread messages.
- 🧳 **Luggage Listing Marketplace**:
   - Sellers publish listings with route, capacity, price per kg, price currency (`USD` / `UZS` / `JPY`), pickup details, and ETA.
   - Buyers reserve storage by kg and provide contact/note details.
   - Sellers can update reservation status (`pending`, `reserved`, `cancelled`).
   - Sellers can edit listings, mark them done/closed, reopen, or delete.
   - Listing availability is computed automatically from `is_active`, expiration, and remaining kg.
- 🤖 **Telegram Notifications**:
   - Secure one-time Telegram linking.
   - Per-listing notification preferences (new reservation, status change, sold out, reopened).
   - Telegram bot webhook support and bot-side subscription controls.
- 💸 **No Platform Fees**: No commissions or hidden charges.
- 🌐 **Multilingual Support**: English, Japanese, Russian, and Uzbek.
- 👤 **Authentication & Account Management**: Django Allauth with social login support.

## 🔁 Luggage Listing Lifecycle

1. Seller creates a listing in `/exchange/luggage/create/`.
2. Buyers reserve available kg on the listing detail page.
3. Seller reviews reservations and updates statuses.
4. Listing state updates automatically:
    - **Open** when active, not expired, and remaining kg > 0.
    - **Closed** when marked done, expired, or fully booked.
5. Seller can edit, reopen, or delete listing when needed.

## 🧭 Main Routes

- `/` — Landing page (money + latest luggage listings)
- `/exchange/create_offer/` — Post money offer
- `/exchange/my_offers/` — My money offers
- `/exchange/luggage/` — Luggage marketplace
- `/exchange/luggage/my/` — My luggage listings
- `/exchange/luggage/notifications/` — My luggage notification settings

## 🌐 Demo

Visit the live demo: [Open Exchange Hub](https://exchangehub.bekhruz.com)

## 🚀 Getting Started

### Prerequisites

- 🐍 Python 3.12+
- 🐘 PostgreSQL
- [Git](https://git-scm.com/)
- [Node.js](https://nodejs.org/) (optional, for frontend development)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/uzbeki/exchange_hub.git
   cd exchange_hub
   ```

2. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:

   Create a `.env` file in the root directory and configure the following variables:

   ```env
   DEBUG=True
   SECRET=your_secret_key
   POSTGRES_DB=exchange_hub
   POSTGRES_USER=your_db_user
   POSTGRES_PASSWORD=your_db_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   EMAIL_HOST=smtp.example.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your_email@example.com
   EMAIL_HOST_PASSWORD=your_email_password

   # Telegram integration (optional, recommended for luggage notifications)
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   TELEGRAM_BOT_USERNAME=your_bot_username_without_at
   TELEGRAM_WEBHOOK_SECRET=your_random_secret
   TELEGRAM_ADMIN_CHAT_ID=optional_admin_chat_id
   ```

5. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

6. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:

   ```bash
   python manage.py runserver
   ```

8. Access the application at `http://127.0.0.1:8000`.

### 🤖 Telegram Webhook Setup (Optional)

After deployment to a public URL, configure the Telegram webhook:

```bash
python manage.py set_telegram_webhook --base-url https://your-domain.example
```

Webhook endpoint used by the command:

- `/exchange/telegram/webhook/`

### 🌍 Translation Commands

Generate translation files:

```bash
py manage.py makemessages --no-wrap -l ja -l uz -l ru --ignore=venv/*
```

Compile translations:

```bash
py manage.py compilemessages --ignore=venv/* -l ja -l uz -l ru
```

### 🧪 Running Tests

To run the test suite:

```bash
python manage.py test
```

### 🌟 Deployment

For production deployment, use a WSGI server like Gunicorn and configure a reverse proxy (e.g., Nginx). Refer to the [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/) for best practices.

## 🤝 Contributing

We welcome contributions! To get started:

1. 🍴 Fork the repository.
2. 🌿 Create a new branch for your feature or bugfix.
3. 💾 Commit your changes and push them to your fork.
4. 🔄 Submit a pull request.

Please ensure your code adheres to the project's coding standards and includes tests where applicable.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📬 Contact

For questions or feedback, please open an issue or contact the project maintainer at [Bekhruz Otaev](uzbekitube@gmail.com).