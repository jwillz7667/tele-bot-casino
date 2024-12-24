from __future__ import annotations

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, select, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
import logging
from datetime import datetime
from typing import Optional, Final, Generator, Any
from dataclasses import dataclass
from contextlib import contextmanager
import sys
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATABASE_URL: Final[str] = "sqlite:///users.db"
LOGGER_FORMAT: Final[str] = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# Configure module logger
logging.basicConfig(
    format=LOGGER_FORMAT,
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path('logs/user_service.log'))
    ]
)

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL statements
    future=True  # Use SQLAlchemy 2.0 style
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

@dataclass
class UserData:
    """Data transfer object for user information"""
    telegram_id: int
    username: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_active: datetime = datetime.utcnow()


class User(Base):
    """
    User model for storing Telegram user information.
    
    Attributes:
        id: Internal database ID
        telegram_id: Unique Telegram user ID
        username: Telegram username
        is_active: Whether the user is active
        created_at: When the user was created
        last_active: When the user was last active
    """
    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    telegram_id: int = Column(Integer, unique=True, index=True, nullable=False)
    username: str = Column(String, index=True)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    last_active: datetime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return (
            f"<User(id={self.id}, "
            f"telegram_id={self.telegram_id}, "
            f"username='{self.username}')>"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary representation"""
        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }


# Create the database tables
Base.metadata.create_all(bind=engine)


class UserService:
    """Service for managing user operations."""
    
    def __init__(self, session_factory: sessionmaker = SessionLocal):
        """
        Initialize the user service.
        
        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory
        logger.info("UserService initialized")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Yields:
            Session: Database session
        
        Raises:
            SQLAlchemyError: If there's a database error
        """
        session = self.session_factory()
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()
    
    async def register_user(self, telegram_id: int, username: str) -> bool:
        """
        Register a new user with their Telegram ID and username.

        Args:
            telegram_id: Unique Telegram ID of the user
            username: Username of the user

        Returns:
            bool: True if registration is successful, False otherwise
        """
        logger.info(f"Attempting to register user {telegram_id}")
        
        try:
            with self.get_session() as session:
                # Check if user already exists
                stmt = select(User).where(User.telegram_id == telegram_id)
                existing_user = session.execute(stmt).scalar_one_or_none()
                
                if existing_user:
                    logger.info(
                        f"User with Telegram ID {telegram_id} already exists",
                        extra={"telegram_id": telegram_id}
                    )
                    return False

                # Create a new user
                new_user = User(telegram_id=telegram_id, username=username)
                session.add(new_user)
                session.commit()
                
                logger.info(
                    f"User {username} registered successfully",
                    extra={
                        "telegram_id": telegram_id,
                        "username": username
                    }
                )
                return True
                
        except SQLAlchemyError as e:
            logger.error(
                f"Database error registering user: {str(e)}",
                exc_info=True,
                extra={
                    "telegram_id": telegram_id,
                    "username": username
                }
            )
            return False
    
    async def is_user_registered(self, telegram_id: int) -> bool:
        """
        Check if a user is already registered.

        Args:
            telegram_id: Unique Telegram ID of the user

        Returns:
            bool: True if user is registered, False otherwise
        """
        try:
            with self.get_session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                user = session.execute(stmt).scalar_one_or_none()
                return user is not None
        except SQLAlchemyError as e:
            logger.error(
                f"Error checking user registration: {str(e)}",
                exc_info=True,
                extra={"telegram_id": telegram_id}
            )
            return False
    
    async def update_last_active(self, telegram_id: int) -> None:
        """
        Update the last active timestamp for a user.

        Args:
            telegram_id: Unique Telegram ID of the user
        """
        try:
            with self.get_session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                user = session.execute(stmt).scalar_one_or_none()
                if user:
                    user.last_active = datetime.utcnow()
                    session.commit()
                    logger.debug(
                        f"Updated last active for user {telegram_id}",
                        extra={"telegram_id": telegram_id}
                    )
        except SQLAlchemyError as e:
            logger.error(
                f"Error updating last active timestamp: {str(e)}",
                exc_info=True,
                extra={"telegram_id": telegram_id}
            )
    
    async def get_user(self, telegram_id: int) -> Optional[UserData]:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: Unique Telegram ID of the user

        Returns:
            Optional[UserData]: User data if found, None otherwise
        """
        try:
            with self.get_session() as session:
                stmt = select(User).where(User.telegram_id == telegram_id)
                user = session.execute(stmt).scalar_one_or_none()
                
                if user:
                    return UserData(
                        telegram_id=user.telegram_id,
                        username=user.username,
                        is_active=user.is_active,
                        created_at=user.created_at,
                        last_active=user.last_active
                    )
                return None
        except SQLAlchemyError as e:
            logger.error(
                f"Error getting user: {str(e)}",
                exc_info=True,
                extra={"telegram_id": telegram_id}
            )
            return None 