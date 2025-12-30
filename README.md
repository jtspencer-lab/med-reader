# Exploration of coding with Visual Code and Copilot

I build a sample Document Signup processing Python application for processing signup documents and utilizing Azure Form Recognizer, spaCy NLP, and PostgreSQL database with a web interface for review.

I started with a single file that read an input file, extracted some data and parked it in a database.

I then utilized Copilot to incrementally evolve the code a complete python stack with code modularity, standard project organization, configuration and erroring handling.

I incrementally used copilot to 
- added error checking and logging
- break into components
- improve handling of API calls
- restructure the project to match Python standards
- add configuration and environment settings

Copilot also created a file that tells how I want copilot to approach my project, 
that file is here    .github\copilot-instructions.md

It's quite impressive how rapidly you reduce the coding drudgery.

## Features

- **Document Processing**: Extract text from medical documents using Azure Form Recognizer
- **NLP Analysis**: Extract patient information using spaCy natural language processing
- **Confidence Scoring**: Automatic confidence scoring for extracted data
- **Human Review**: Web interface for reviewing low-confidence extractions
- **Database Storage**: PostgreSQL database for storing documents and patient data
- **REST API**: FastAPI-based API for integration with other systems
- **Batch Processing**: Process multiple documents in batch mode

## Architecture

The application follows Python best practices with a layered architecture:

```
app/
├── api/           # API routes and endpoints
├── services/      # Business logic layer
├── models/        # Data models and schemas
├── database/      # Database layer and repositories
├── web/           # Web interface routes and templates
├── core/          # Core application components
└── utils/         # Utility functions
```

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Azure Form Recognizer account
- spaCy model (`en_core_web_sm`)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MedDocReader
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Initialize database**
   ```bash
   python scripts/init_db.py
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=healthcare_db
DB_USER=db_user
DB_PASSWORD=db_pass

# Azure Configuration
AZURE_FORM_RECOGNIZER_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_FORM_RECOGNIZER_KEY=your-key

# Application Configuration
DEBUG=False
SECRET_KEY=your-secret-key
LOG_LEVEL=INFO
```

## Usage

### Running the Application

```bash
# Development mode
python app/main.py

# Production mode with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Web Interface

Access the web interface at `http://localhost:8000`:

- **Dashboard**: Overview of processing status
- **Upload**: Upload documents for processing
- **Review**: Review documents with low confidence scores
- **API Documentation**: Available at `/docs`

### API Endpoints

- `GET /api/documents` - List all documents
- `GET /api/documents/{id}` - Get specific document
- `POST /api/process-batch` - Process batch of documents
- `POST /upload` - Upload single document

### Batch Processing

```python
from app.services import DocumentProcessingService

service = DocumentProcessingService()
results = service.process_batch("path/to/documents")
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual image
docker build -t meddocreader .
docker run -p 8000:8000 meddocreader
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/
flake8 app/
mypy app/
```

### Database Migrations

```bash
python scripts/migrate.py
```

## Project Structure

```
MedDocReader/
├── app/                    # Main application package
│   ├── api/               # API routes
│   ├── services/          # Business logic
│   ├── models/            # Data models
│   ├── database/          # Database layer
│   ├── web/              # Web interface
│   ├── core/             # Core components
│   └── utils/             # Utilities
├── tests/                 # Test suite
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── requirements.txt       # Dependencies
├── docker-compose.yml     # Docker configuration
└── README.md             # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please open an issue in the repository.

