import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from pytest import FixtureRequest
from _pytest.fixtures import FixtureFunction

from src.user_service import UserService, User, Base

@pytest.fixture
def engine() -> Engine:
    """Create a test database engine."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session_factory(engine: Engine) -> sessionmaker:
    """Create a test session factory."""
    factory = sessionmaker()
    factory.configure(bind=engine)
    return factory

@pytest.fixture
def user_service(session_factory: sessionmaker) -> UserService:
    """Create a test user service."""
    return UserService(session_factory)

@pytest.mark.asyncio
async def test_register_user(user_service: UserService):
    """Test registering a new user."""
    # Register a new user
    success = await user_service.register_user(telegram_id=123456)
    assert success is True
    
    # Try to register the same user again
    success = await user_service.register_user(telegram_id=123456)
    assert success is True  # Should return True for already registered users
    
    # Verify user exists
    user = await user_service.get_user(telegram_id=123456)
    assert user is not None
    assert user.telegram_id == 123456

@pytest.mark.asyncio
async def test_is_user_registered(user_service: UserService):
    """Test checking if a user is registered."""
    # Check unregistered user
    is_registered = await user_service.is_user_registered(telegram_id=123456)
    assert is_registered is False
    
    # Register user
    await user_service.register_user(telegram_id=123456)
    
    # Check registered user
    is_registered = await user_service.is_user_registered(telegram_id=123456)
    assert is_registered is True

@pytest.mark.asyncio
async def test_update_last_active(user_service: UserService):
    """Test updating user's last active timestamp."""
    # Register user
    await user_service.register_user(telegram_id=123456)
    
    # Get initial last active time
    user = await user_service.get_user(telegram_id=123456)
    initial_last_active = user.last_active
    
    # Wait a moment
    await asyncio.sleep(0.1)
    
    # Update last active
    success = await user_service.update_last_active(telegram_id=123456)
    assert success is True
    
    # Verify last active was updated
    user = await user_service.get_user(telegram_id=123456)
    assert user.last_active > initial_last_active

@pytest.mark.asyncio
async def test_get_user(user_service: UserService):
    """Test getting a user by Telegram ID."""
    # Try to get non-existent user
    user = await user_service.get_user(telegram_id=123456)
    assert user is None
    
    # Register user
    await user_service.register_user(telegram_id=123456)
    
    # Get existing user
    user = await user_service.get_user(telegram_id=123456)
    assert user is not None
    assert user.telegram_id == 123456

@pytest.mark.asyncio
async def test_error_handling(user_service: UserService, session_factory: sessionmaker):
    """Test error handling in user service."""
    # Close the engine to simulate database errors
    session_factory.kw['bind'].dispose()
    
    # Verify operations fail gracefully
    success = await user_service.register_user(telegram_id=123456)
    assert success is False
    
    is_registered = await user_service.is_user_registered(telegram_id=123456)
    assert is_registered is False
    
    success = await user_service.update_last_active(telegram_id=123456)
    assert success is False
    
    user = await user_service.get_user(telegram_id=123456)
    assert user is None 