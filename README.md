# Open Exchange Hub

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2-green)](https://www.djangoproject.com/)

🌍 **Open Exchange Hub** is a peer-to-peer platform designed to connect Uzbek expats and others who need to exchange currencies (e.g., 💴 JPY, 🇺🇿 UZS, 💵 USD) between Uzbekistan and other countries. The platform facilitates direct connections, allowing users to bypass traditional bank fees and transfer service commissions.

## ✨ Features

- 📝 **Post Offers**: Create offers to send or receive money with your preferred terms.
- 🔒 **Secure Chat**: Connect with other users via a secure chat system.
- 💸 **No Fees**: Exchange money without any commissions or hidden charges.
- 🌐 **Multilingual Support**: Available in English, Japanese, Russian, and Uzbek.
- 👤 **User Authentication**: Secure login and account management with Django Allauth.

## 🌐 Demo

Visit the live demo: [Open Exchange Hub](https://exchangehub.bekhruz.com)

## 🚀 Getting Started

### Prerequisites

- 🐍 Python 3.10+
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