import os
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)

# IMPORTANT: Do not crash on import if MASTER_KEY is missing, so /health still works.
# We validate lazily when encrypt/decrypt are actually used.
_f = None
_key_error = None

MASTER_KEY = os.getenv('MASTER_KEY')
if MASTER_KEY:
	try:
		# MASTER_KEY must be a urlsafe base64-encoded 32-byte key (Fernet.generate_key()).
		# Accept both bytes-like and str. Environment variables are str.
		_f = Fernet(MASTER_KEY.encode() if not isinstance(MASTER_KEY, (bytes, bytearray)) else MASTER_KEY)
	except Exception as e:  # ValueError for invalid key format
		_key_error = e
		logger.error("MASTER_KEY is invalid. Provide a Fernet key (base64 urlsafe 32 bytes).", exc_info=False)
else:
	logger.error("MASTER_KEY is not set. Secrets endpoints will fail until configured.")


def _ensure_key_ready():
	if _f is None:
		if MASTER_KEY is None:
			raise RuntimeError('MASTER_KEY is not set. Set a Fernet key in environment (Fernet.generate_key()).')
		raise RuntimeError(f'MASTER_KEY is invalid: {_key_error}')


def encrypt(s: str) -> str:
	_ensure_key_ready()
	return _f.encrypt(s.encode()).decode()


def decrypt(s: str) -> str:
	_ensure_key_ready()
	try:
		return _f.decrypt(s.encode()).decode()
	except InvalidToken as e:
		raise RuntimeError('Failed to decrypt secret: invalid token or key.') from e
