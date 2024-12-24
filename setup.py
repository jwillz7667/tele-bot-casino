from setuptools import setup, find_packages

setup(
    name="telegram-casino-bot",
    version="0.1.0",
    description="A Telegram bot for managing virtual casino games and user wallets",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot>=20.7",
        "SQLAlchemy>=2.0.25",
        "python-dotenv>=1.0.0",
        "alembic>=1.13.1"
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "isort>=5.13.2",
            "mypy>=1.8.0",
            "pylint>=3.0.3"
        ]
    },
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "casino-bot=src.bot:main"
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Chat",
        "Topic :: Games/Entertainment",
        "Framework :: AsyncIO",
        "Framework :: Pytest"
    ]
) 