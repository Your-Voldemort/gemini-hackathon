# Environment Configuration Guide

## .env.local Setup

The LegalMind project uses `.env.local` for local secret management. This file is **NOT** committed to version control.

### Creating .env.local

A `.env.local` file has been created in the `backend/` directory with your API key. This file:

1. **Contains sensitive credentials** (API keys, project IDs)
2. **Is ignored by git** (see `.gitignore`)
3. **Is loaded automatically** when running `python main_new.py`

### File Locations

- **Backend**: `backend/.env.local` - Contains Gemini API key and Google Cloud credentials
- **Reference**: `backend/.env.example` - Template showing all available configuration options

### How It Works

1. When you run `python main_new.py`, it automatically loads:
   - `.env.local` first (highest priority - your local secrets)
   - `.env` second (if .env.local doesn't exist)

2. Environment variables are read by Pydantic `BaseSettings` in `backend/config/settings.py`

3. Settings are accessed throughout the application via:
   ```python
   from config.settings import get_settings
   settings = get_settings()
   ```

### Updating Configuration

To change any configuration:

1. Edit `backend/.env.local` with your values
2. Restart the backend server (`python main_new.py`)
3. Changes take effect immediately

### Running the Project

```bash
# Terminal 1: Backend
cd backend
python main_new.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

**No API keys needed on the command line** - they're read from `.env.local`

### Project Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Important Security Notes

⚠️ **DO NOT:**
- Commit `.env.local` to git
- Share your API keys in chat, emails, or pull requests
- Use the same API key across different environments

✅ **DO:**
- Keep `.env.local` in your local `.gitignore`
- Rotate API keys regularly
- Use project-specific credentials
