import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load variables from the project's .env file into os.environ BEFORE any
# config value is read. Without this, DATABASE_URL / POSTGRES_* / Supabase
# credentials placed in .env are ignored and the hardcoded defaults are used.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, '.env'))
except ImportError:
    # python-dotenv not installed yet; env vars must be set in the shell.
    pass


def _ensure_sslmode(db_url):
    """Supabase (and most managed Postgres) require SSL. Append
    sslmode=require for remote hosts when the caller did not specify one."""
    lowered = db_url.lower()
    if 'sslmode=' in lowered:
        return db_url
    # Only force SSL for remote databases, never for a local dev server.
    if 'localhost' in lowered or '127.0.0.1' in lowered:
        return db_url
    separator = '&' if '?' in db_url else '?'
    return f"{db_url}{separator}sslmode=require"

def get_database_uri():
    """
    Constructs and normalizes PostgreSQL database connectivity URI.
    Supports:
    - DATABASE_URL environment variable (handles 'postgres://' vs 'postgresql://')
    - Discrete environment variables: POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
    - Defaults to PostgreSQL on localhost:5432/campus_rental
    - Supports explicit USE_SQLITE=1 override or automatic local fallback.
    """
    if os.environ.get('USE_SQLITE', '').lower() in ('1', 'true', 'yes'):
        return f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'campus_rental.db')}"

    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # Normalize Heroku/Supabase postgres:// dialect prefix
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
        elif db_url.startswith('postgresql://') and '+psycopg2' not in db_url and '+pg8000' not in db_url:
            db_url = db_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        return _ensure_sslmode(db_url)

    pg_user = os.environ.get('POSTGRES_USER', 'postgres')
    pg_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
    pg_port = os.environ.get('POSTGRES_PORT', '5432')
    pg_db = os.environ.get('POSTGRES_DB', 'campus_rental')

    return _ensure_sslmode(
        f"postgresql+psycopg2://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"
    )


class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'campus-smart-rental-secret-key-2026-secure')

    # Primary Database: PostgreSQL (with automatic connection pooling)
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

    # Campus Rental Settings
    DEFAULT_CURRENCY = '₹'
    LATE_FINE_PER_DAY = 50.0  # ₹50 per day overdue
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')

    # Razorpay Payment Gateway Configuration
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_1DP5mmOlF5G5ag')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 't7J9kF2mN8pQ4sV6')
