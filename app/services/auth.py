from pwdlib import PasswordHash


# istanza di PasswordHash con Argon2 come hasher
password_hash = PasswordHash.recommended()

# funzione di MATCH tra PWD IN CHIARO (input utente) e PWD HASHATA salvata nel DB
def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# funzione per CREARE HASH di una PWD IN CHIARO
def get_password_hash(password: str | bytes) -> str:
    return password_hash.hash(password)