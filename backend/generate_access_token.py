from fyers_apiv3 import fyersModel
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv("FYERS_CLIENT_ID")
secret_key = os.getenv("FYERS_SECRET_KEY")
redirect_uri = os.getenv("FYERS_REDIRECT_URI")

session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type="code",
    grant_type="authorization_code"
)

print("\nOpen this URL in your browser:\n")
print(session.generate_authcode())