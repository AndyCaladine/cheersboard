import os
from dotenv import load_dotenv
 
load_dotenv()
 
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    DATABASE = os.path.join(os.getcwd(), "instance", "database.db")
 
    # Stripe
    STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY", "")
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
 
    # Board pricing in pence
    PRICE_LITE_PENCE = 499
    PRICE_PREMIUM_PENCE = 999
    PRICE_EVENT_PENCE = 1999
 
    # Terms and GDPR document versions
    # Update these when documents change to trigger re-consent prompts
    TERMS_VERSION = "1.0"
    GDPR_VERSION = "1.0"
 