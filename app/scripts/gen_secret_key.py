import secrets


def generate_secret_key(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def main() -> None:
    key = generate_secret_key()
    print(f"Generated key: {key}")


if __name__ == "__main__":
    main()
