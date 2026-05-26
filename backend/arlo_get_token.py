"""
One-time Arlo token setup script.
Run this in your terminal to get a session token you can store in Vercel.

  python3 arlo_get_token.py

You will be prompted for your Arlo email, password, and the SMS code.
The script prints an ARLO_TOKEN value — paste it into Vercel env vars.
"""

import urllib.request
import urllib.error
import http.cookiejar
import json
import sys
import getpass

AUTH_URL  = "https://ocapi-app.arlo.com/api/auth"
START_URL = "https://ocapi-app.arlo.com/api/startAuth"
FINISH_URL = "https://ocapi-app.arlo.com/api/finishAuth"

HEADERS = {
    "Content-Type": "application/json",
    "Referer": "https://my.arlo.com/",
    "schemaVersion": "1",
    "DNT": "1",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Origin": "https://my.arlo.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}


def request(opener, url, body=None, method=None):
    data = json.dumps(body).encode() if body else None
    m = method or ("POST" if data else "GET")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=m)
    try:
        resp = opener.open(req, timeout=20)
        return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:
        return None, str(e)


def main():
    print("=== Arlo Token Setup ===\n")
    email = input("Arlo email: ").strip()
    password = getpass.getpass("Arlo password: ")

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    print("\nLogging in...")
    data, err = request(opener, AUTH_URL, {
        "email": email, "password": password,
        "language": "en", "EnvType": "prod"
    })
    if err:
        print(f"Login error: {err}")
        sys.exit(1)

    body = data.get("data", {})
    if body.get("authenticated"):
        token = body.get("token")
        print(f"\n✓ Logged in (no 2FA needed)\n\nARLO_TOKEN={token}")
        return

    # 2FA required — find SMS factor
    factors = body.get("factors", [])
    sms_factor = next(
        (f for f in factors if f.get("factorType", "").upper() == "SMS"), None
    )
    if not sms_factor:
        email_factor = next(
            (f for f in factors if f.get("factorType", "").upper() in ("EMAIL", "MAIL")), None
        )
        sms_factor = email_factor
        if sms_factor:
            print("SMS 2FA not found — using email 2FA instead")

    if not sms_factor:
        print(f"No supported 2FA factor found. Available: {[f.get('factorType') for f in factors]}")
        sys.exit(1)

    factor_id = sms_factor.get("factorId")
    print(f"\n2FA required ({sms_factor.get('factorType')}). Sending code...")
    data, err = request(opener, START_URL, {"factorId": factor_id})
    if err:
        print(f"Failed to start 2FA: {err}")
        sys.exit(1)

    factor_auth_code = data.get("data", {}).get("factorAuthCode", "")
    code = input("Enter the code from your SMS/email: ").strip()

    print("Verifying...")
    data, err = request(opener, FINISH_URL, {
        "factorAuthCode": factor_auth_code,
        "otp": code
    })
    if err:
        print(f"Verification error: {err}")
        sys.exit(1)

    body = data.get("data", {})
    if not body.get("authenticated"):
        print("Verification failed — check the code and try again.")
        sys.exit(1)

    token = body.get("token")
    print(f"\n✓ Authenticated!\n")
    print("=" * 60)
    print(f"ARLO_TOKEN={token}")
    print("=" * 60)
    print("\nAdd this as an environment variable in Vercel:")
    print("  vercel.com → home-hub → Settings → Environment Variables")
    print("  Key: ARLO_TOKEN   Value: (paste the token above)")


if __name__ == "__main__":
    main()
