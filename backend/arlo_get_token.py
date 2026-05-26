"""
One-time Arlo token setup script.
Run this to get a session token to store in Vercel.

  pip3 install curl_cffi
  python3 arlo_get_token.py

You will be prompted for your Arlo email, password, and the SMS code.
The script prints an ARLO_TOKEN — paste it back into Claude.
"""

import json
import sys
import getpass

AUTH_URL   = "https://ocapi-app.arlo.com/api/auth"
START_URL  = "https://ocapi-app.arlo.com/api/startAuth"
FINISH_URL = "https://ocapi-app.arlo.com/api/finishAuth"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://my.arlo.com/",
    "Origin": "https://my.arlo.com",
    "schemaVersion": "1",
    "DNT": "1",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_session():
    try:
        from curl_cffi import requests
        print("✓ Using curl_cffi (Chrome TLS impersonation)")
        session = requests.Session(impersonate="chrome120")
        session.headers.update(HEADERS)
        return session, "curl_cffi"
    except ImportError:
        print("curl_cffi not found — install it first:")
        print("  pip3 install curl_cffi")
        sys.exit(1)


def post(session, url, body):
    resp = session.post(url, json=body, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def main():
    print("=== Arlo Token Setup ===\n")
    email    = input("Arlo email: ").strip()
    password = getpass.getpass("Arlo password: ")

    session, _ = get_session()

    print("\nLogging in to Arlo...")
    try:
        data = post(session, AUTH_URL, {
            "email": email,
            "password": password,
            "language": "en",
            "EnvType": "prod",
        })
    except RuntimeError as e:
        print(f"\n✗ Login failed: {e}")
        sys.exit(1)

    body = data.get("data", {})

    if body.get("authenticated"):
        token = body["token"]
        _print_token(token)
        return

    # 2FA required
    factors = body.get("factors", [])
    print(f"\n2FA required. Available factors: {[f.get('factorType') for f in factors]}")

    # Prefer SMS, fall back to email
    factor = next(
        (f for f in factors if f.get("factorType", "").upper() == "SMS"),
        next((f for f in factors if "MAIL" in f.get("factorType", "").upper()), None),
    )

    if not factor:
        print("No SMS or email 2FA factor found.")
        print(f"Raw response:\n{json.dumps(data, indent=2)}")
        sys.exit(1)

    factor_id = factor["factorId"]
    print(f"\nSending code via {factor.get('factorType')}...")

    data2 = post(session, START_URL, {"factorId": factor_id})
    factor_auth_code = data2.get("data", {}).get("factorAuthCode", "")

    if not factor_auth_code:
        print(f"Unexpected startAuth response:\n{json.dumps(data2, indent=2)}")
        sys.exit(1)

    code = input("Enter the code from your SMS: ").strip()

    print("Verifying...")
    data3 = post(session, FINISH_URL, {
        "factorAuthCode": factor_auth_code,
        "otp": code,
    })

    body3 = data3.get("data", {})
    if not body3.get("authenticated"):
        print(f"✗ Verification failed:\n{json.dumps(data3, indent=2)}")
        sys.exit(1)

    _print_token(body3["token"])


def _print_token(token: str):
    print("\n" + "=" * 60)
    print("✓  SUCCESS — paste this token back into Claude:")
    print("=" * 60)
    print(f"\nARLO_TOKEN={token}\n")
    print("=" * 60)


if __name__ == "__main__":
    main()
