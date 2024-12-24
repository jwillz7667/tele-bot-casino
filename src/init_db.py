from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import os

from user_service import Base, User
from wallet.transaction import Transaction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with required tables."""
    try:
        # Get database URL from environment variable
        database_url = os.getenv('DATABASE_URL', 'sqlite:///casino.db')
        
        # Create engine
        engine = create_engine(database_url)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session factory
        Session = sessionmaker(bind=engine)
        
        logger.info("Database initialized successfully")
        return Session
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

if __name__ == '__main__':
    init_db() 