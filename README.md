# MailMind

An intelligent email analytics application that connects to Gmail, analyzes communication patterns, ranks contacts by friendliness, and allows natural language queries over email history.

## 🎯 Features

- **Gmail Integration**: Connect via MCP (Model Context Protocol) or OAuth 2.0
- **Data Analytics**: Contact ranking, friendliness scoring, time-based trends
- **AI Query Interface**: Natural language queries with RAG-powered responses
- **Export & Sharing**: PDF, CSV, JSON exports with optional anonymization

## 🏗️ Architecture

The project follows a modular architecture with clear separation of concerns:

```
mailmind/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Core configuration and utilities
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   ├── api/            # API routes
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend (future)
├── database/               # Database migrations and schemas
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- Gmail API credentials

### Backend Setup

1. **Clone and setup environment:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

3. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup (Future)

```bash
cd frontend
npm install
npm start
```

## 🔧 Configuration

Create a `.env` file in the backend directory:

```env
# Database
DATABASE_URL=sqlite:///./mailmind.db

# Gmail API
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret

# OpenAI API
OPENAI_API_KEY=your_openai_key

# MCP Configuration
MCP_SERVER_URL=your_mcp_server_url
```

## 📊 Database Schema

The application uses SQLite with the following main entities:
- Users
- Emails
- Contacts
- Analytics
- Queries

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details
