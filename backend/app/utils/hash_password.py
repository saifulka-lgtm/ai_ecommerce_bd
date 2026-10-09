"""Create a hash for ADMIN_PASSWORD_HASH:

    python -m app.utils.hash_password

Paste the printed line into backend/.env (and remove ADMIN_PASSWORD)."""
import getpass

from app.services.auth_service import hash_password

if __name__ == "__main__":
    pw = getpass.getpass("New admin password: ")
    if len(pw) < 10:
        raise SystemExit("Use at least 10 characters.")
    if pw != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match.")
    print(f"ADMIN_PASSWORD_HASH={hash_password(pw)}")
