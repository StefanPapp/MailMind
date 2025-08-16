# MailMind Backend

FastAPI backend for the MailMind email analytics application.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Virtual environment (recommended)

### Setup

1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

4. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

### Running the Application

**Option 1: Using the startup script**
```bash
python start.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 3: Using the test script**
```bash
python test_server.py
```

### Accessing the Application

- **API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **Root Endpoint**: http://localhost:8000/

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./mailmind.db

# Gmail API
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4

# MCP Configuration
MCP_SERVER_URL=your_mcp_server_url
MCP_API_KEY=your_mcp_api_key

# Security
SECRET_KEY=your_secret_key_here_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Development
DEBUG=True
LOG_LEVEL=INFO
```

## 🧪 Testing

Run the test suite:
```bash
pytest tests/
```

Run specific tests:
```bash
pytest tests/test_basic.py -v
```

## 📊 Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migrations:
```bash
alembic downgrade -1
```

## 🔍 Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'sqlalchemy'**
   - Make sure you're using the virtual environment
   - Run: `source venv/bin/activate && pip install -r requirements.txt`

2. **ModuleNotFoundError: No module named 'jwt'**
   - Install PyJWT: `pip install PyJWT`

3. **Database connection errors**
   - Check your DATABASE_URL in .env
   - Ensure the database directory is writable

4. **Import errors**
   - Make sure all dependencies are installed
   - Check that you're in the correct directory (backend/)

### Debug Mode

Enable debug mode in your `.env` file:
```env
DEBUG=True
LOG_LEVEL=DEBUG
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── core/           # Configuration and database
│   ├── models/         # Database models
│   ├── services/       # Business logic
│   ├── api/            # API routes
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── alembic/            # Database migrations
├── requirements.txt    # Python dependencies
├── start.py           # Application startup script
└── test_server.py     # Server test script
```

## 🔗 API Endpoints

### Authentication
- `POST /api/v1/auth/gmail/authorize` - Initiate Gmail OAuth
- `POST /api/v1/auth/gmail/callback` - Handle OAuth callback
- `POST /api/v1/auth/token` - Get access token
- `GET /api/v1/auth/me` - Get current user

### Emails
- `GET /api/v1/emails/` - List emails
- `GET /api/v1/emails/{email_id}` - Get email details
- `POST /api/v1/emails/sync` - Sync emails from provider
- `GET /api/v1/emails/analytics/sentiment` - Sentiment analytics
- `GET /api/v1/emails/analytics/trends` - Email trends

### Contacts
- `GET /api/v1/contacts/` - List contacts
- `GET /api/v1/contacts/rankings` - Contact rankings
- `GET /api/v1/contacts/{contact_id}` - Get contact details
- `PUT /api/v1/contacts/{contact_id}/favorite` - Toggle favorite
- `GET /api/v1/contacts/analytics/friendliness` - Friendliness analytics

### AI Queries
- `POST /api/v1/ai/query` - Process natural language query
- `GET /api/v1/ai/suggestions` - Get query suggestions
- `POST /api/v1/ai/summarize` - Generate data summary
- `GET /api/v1/ai/capabilities` - Get AI capabilities

## 🚀 Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Use a production database (PostgreSQL recommended)
3. Configure proper CORS settings
4. Set up proper logging
5. Use a production WSGI server (Gunicorn + Uvicorn)

Example production command:
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
