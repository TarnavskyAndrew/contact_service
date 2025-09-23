import json
from datetime import datetime, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from src.conf.config import settings

# вставити сюди токен
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJOb3JiZXJ0X0h5YXR0MzNAeWFob28uY29tIiwic2NvcGUiOiJyZXNldF9wYXNzd29yZCIsImV4cCI6MTc1NzA4MDIyNn0.GmaTMHXrTvddugSej_DcSyyQIxrGs23m2EE_NKJBtBw"


def detect_token_type(payload: dict) -> str:
    """
    Detect the type of a JWT token based on its payload.

    :param payload: Decoded JWT payload.
    :type payload: dict
    :return: Human-readable token type (Access, Refresh, Email Verify, Password Reset, or Unknown).
    :rtype: str
    """
    scope = payload.get("scope")
    if scope == "access_token":
        return "Access Token"
    elif scope == "refresh_token":
        return "Refresh Token"
    elif scope == "email_verify":
        return "Email Verification Token"
    elif scope == "reset_password":
        return "Password Reset Token"
    else:
        return "Unknown / Custom Token"


def parse_token(token: str) -> dict:
    
    """
    Parse and validate a JSON Web Token (JWT).

    Decodes the JWT, extracts header and payload, determines token type,
    and converts the expiration timestamp into a human-readable format.

    :param token: Encoded JWT string.
    :type token: str
    :return: A dictionary with token information, including status, header, payload,
             token type, and human-readable expiration time (if available).
    :rtype: dict
    :raises jose.JWTError: If the token is invalid.
    :raises jose.ExpiredSignatureError: If the token has expired.
    """
    
    try:
        # Заголовок (без верифікації)
        header = jwt.get_unverified_header(token)

        # Payload (з верифікацією)
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Тип токена
        token_type = detect_token_type(payload)

        # Час для exp (якщо є)
        exp = payload.get("exp")
        exp_human = None
        if exp:
            try:
                exp_dt = datetime.fromtimestamp(int(exp), tz=timezone.utc)
                exp_human = exp_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
            except Exception:
                exp_human = str(exp)

        return {
            "status": "ok",
            "header": header,
            "payload": payload,
            "token_type": token_type,
            "exp_human": exp_human,
        }
    except ExpiredSignatureError:
        return {"status": "error", "error": "Token expired"}
    except JWTError as e:
        return {"status": "error", "error": f"Invalid token: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    
    """
    CLI entry point for decoding a JWT.

    Usage:
        poetry run python parse_jwt.py

    Steps:
        1. Paste your JWT into the ``JWT_TOKEN`` variable at the top of this file.
        2. Run the script with Poetry or Python.
        3. The script will output the header, payload, token type, expiration,
           and a raw JSON dump.

    Example:
        >>> poetry run python parse_jwt.py
    """
    
    if not JWT_TOKEN or JWT_TOKEN.startswith("eyJhbGciOiJIUzI1Ni"):
        print("Paste your JWT into the JWT_TOKEN variable at the top of the file.")
    else:
        result = parse_token(JWT_TOKEN)

        print("\n================= JWT INFO =================")
        if result["status"] == "ok":
            print("Header:")
            print(json.dumps(result["header"], indent=2, ensure_ascii=False))

            print("\nPayload:")
            print(json.dumps(result["payload"], indent=2, ensure_ascii=False))

            print(f"\nToken type: {result['token_type']}")

            if result.get("exp_human"):
                print(f"Expires at: {result['exp_human']}")
        else:
            print(" Error:", result["error"])

        print("\n================= RAW JSON =================")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
