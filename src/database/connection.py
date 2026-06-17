import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RRM.Database")

# Load environment variables
load_dotenv()

# Determine database URL with SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to local SQLite file
    sqlite_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../rrm_database.db"))
    DATABASE_URL = f"sqlite:///{sqlite_db_path}"
    logger.info(f"DATABASE_URL not specified. Falling back to SQLite at: {sqlite_db_path}")
else:
    logger.info(f"Connecting to database configured in DATABASE_URL")

# Create SQLAlchemy engine
# SQLite requires 'check_same_thread' set to False for FastAPI background worker threads
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True  # Automatically checks connection health before issuing queries
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base model class
Base = declarative_base()

def get_db():
    """
    Dependency helper function to get db session.
    Ensures that sessions are properly closed after operations.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initializes database schemas.
    """
    try:
        logger.info("Initializing database schemas...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database schemas: {e}")
        raise
