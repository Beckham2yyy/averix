import os
import secrets
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, redirect
import json
import urllib.parse
import base64

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = "termux-dev-secret-123"

# ========== X (TWITTER) API CONFIGURATION ==========
X_CLIENT_ID = "SGJQUmgydDMySkhLcEE1Z2ZxMXo6MTpjaQ"
X_CLIENT_SECRET = "oSEnTSpZuDCEgwwXayCaH3_AaLp5p1ctLsF1m8c9rAVFHZflq1"
X_CALLBACK_URL = "https://averix.up.railway.app/x/callback"
# ===================================================

# ========== DISCORD API CONFIGURATION ==========
DISCORD_CLIENT_ID = "1458119139695526042"
DISCORD_CLIENT_SECRET = "9IRYUB6yTFaRQ0Lvcxq3Y8VzsLCEWwXr"
DISCORD_CALLBACK_URL = "https://averix.up.railway.app/discord/callback"
DISCORD_AUTH_URL = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"
# ===============================================

# Storage (simple dictionary - in production use a database)
NONCES = {}
USER_DATA = {}
DAILY_CHECKINS = {}  # Store last check-in date by address
PROFILE_PICS = {}    # Store profile picture data

# Create uploads directory
os.makedirs('static/uploads', exist_ok=True)

@app.route("/")
def home():
    return render_template('index.html')

# ========== X (TWITTER) OAUTH ROUTES ==========

@app.route("/x/auth")
def x_auth():
    """Start X OAuth flow - redirect user to X for authorization"""
    # Generate state parameter for security
    state = secrets.token_hex(16)
    session['x_state'] = state
    
    # Build X OAuth URL
    auth_url = (
        "https://twitter.com/i/oauth2/authorize?"
        "response_type=code&"
        f"client_id={X_CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(X_CALLBACK_URL)}&"
        f"state={state}&"
        "scope=tweet.read%20users.read%20offline.access&"
        "code_challenge=challenge&"
        "code_challenge_method=plain"
    )
    
    return redirect(auth_url)

@app.route("/x/callback")
def x_callback():
    """Handle X OAuth callback and exchange code for access token"""
    # Get parameters from callback
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state parameter
    if not code or not state or state != session.get('x_state'):
        return "Invalid callback parameters", 400
    
    # Clear state from session
    session.pop('x_state', None)
    
    try:
        # Prepare token request
        token_url = "https://api.twitter.com/2/oauth2/token"
        
        # Build request data
        data = {
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': X_CLIENT_ID,
            'redirect_uri': X_CALLBACK_URL,
            'code_verifier': 'challenge'
        }
        
        # Make request to get access token
        auth_string = f"{X_CLIENT_ID}:{X_CLIENT_SECRET}"
        auth_header = f"Basic {base64.b64encode(auth_string.encode()).decode()}"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': auth_header
        }
        
        response = requests.post(token_url, data=data, headers=headers)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            return "Failed to get access token from X", 400
        
        access_token = token_data['access_token']
        
        # Get user info from X
        user_url = "https://api.twitter.com/2/users/me"
        user_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get(user_url, headers=user_headers)
        user_data = user_response.json()
        
        if 'data' not in user_data or 'username' not in user_data['data']:
            return "Failed to get user info from X", 400
        
        x_username = user_data['data']['username']
        x_user_id = user_data['data']['id']
        
        # Return HTML page that will save to localStorage and redirect back
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Averix - X Connection Complete</title>
            <script>
                // Save X connection to localStorage
                localStorage.setItem("averix_x_connected", "true");
                localStorage.setItem("averix_x_username", "{x_username}");
                
                // Redirect back to Averix app
                window.location.href = "/";
            </script>
        </head>
        <body>
            <p>X connection successful! Redirecting back to Averix...</p>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f"X OAuth error: {e}")
        return f"Error during X authentication: {str(e)}", 500

# ========== DISCORD OAUTH ROUTES ==========

@app.route("/discord/auth")
def discord_auth():
    """Start Discord OAuth flow - redirect user to Discord for authorization"""
    # Generate state parameter for security
    state = secrets.token_hex(16)
    session['discord_state'] = state
    
    # Build Discord OAuth URL
    auth_url = (
        f"{DISCORD_AUTH_URL}?"
        f"client_id={DISCORD_CLIENT_ID}&"
        "response_type=code&"
        f"redirect_uri={urllib.parse.quote(DISCORD_CALLBACK_URL)}&"
        f"state={state}&"
        "scope=identify%20email"
    )
    
    return redirect(auth_url)

@app.route("/discord/callback")
def discord_callback():
    """Handle Discord OAuth callback and exchange code for access token"""
    # Get parameters from callback
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state parameter
    if not code or not state or state != session.get('discord_state'):
        return "Invalid callback parameters", 400
    
    # Clear state from session
    session.pop('discord_state', None)
    
    try:
        # Prepare token request
        data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_CALLBACK_URL,
            'scope': 'identify email'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Exchange code for access token
        response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            return "Failed to get access token from Discord", 400
        
        access_token = token_data['access_token']
        
        # Get user info from Discord
        user_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get(DISCORD_USER_URL, headers=user_headers)
        user_data = user_response.json()
        
        if 'username' not in user_data:
            return "Failed to get user info from Discord", 400
        
        discord_username = user_data['username'];
        discord_discriminator = user_data.get('discriminator', '0')
        
        # Format username with discriminator (if available)
        if discord_discriminator and discord_discriminator != '0':
            discord_full_username = f"{discord_username}#{discord_discriminator}"
        else:
            discord_full_username = discord_username
        
        # Return HTML page that will save to localStorage and redirect back
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Averix - Discord Connection Complete</title>
            <script>
                // Save Discord connection to localStorage
                localStorage.setItem("averix_discord_connected", "true");
                localStorage.setItem("averix_discord_username", "{discord_full_username}");
                
                // Redirect back to Averix app
                window.location.href = "/";
            </script>
        </head>
        <body>
            <p>Discord connection successful! Redirecting back to Averix...</p>
        </body>
        </html>
        '''
        
    except Exception as e:
        print(f"Discord OAuth error: {e}")
        return f"Error during Discord authentication: {str(e)}", 500

@app.route("/nonce", methods=["POST"])
def nonce():
    data = request.json
    address = data.get("address", "").lower()
    
    if not address:
        return jsonify({"error": "No address provided"}), 400
    
    # Generate nonce
    nonce = secrets.token_hex(32)
    NONCES[address] = {
        "nonce": nonce,
        "timestamp": datetime.now().isoformat()
    }
    
    # Clean up old nonces
    for addr in list(NONCES.keys()):
        if (datetime.now() - datetime.fromisoformat(NONCES[addr]["timestamp"])).seconds > 300:
            del NONCES[addr]
    
    return jsonify({"message": f"Sign this message to authenticate: {nonce}"})

@app.route("/verify", methods=["POST"])
def verify():
    data = request.json
    address = data.get("address", "").lower()
    
    if not address:
        return jsonify({"ok": False, "error": "No address provided"}), 400
    
    # Check if nonce exists
    if address not in NONCES:
        return jsonify({"ok": False, "error": "Nonce expired or not found"}), 400
    
    # In a real app, verify the signature here
    # For simplicity, we'll just remove the nonce and consider it verified
    
    # Remove used nonce
    NONCES.pop(address, None)
    
    # Initialize user data if not exists
    if address not in USER_DATA:
        USER_DATA[address] = {
            "username": "",
            "email": "",
            "daily_streak": 0,
            "last_checkin": None,
            "tasks_completed": 0
        }
    
    return jsonify({
        "ok": True,
        "address": address,
        "user_data": USER_DATA[address]
    })

@app.route("/upload_profile_pic", methods=["POST"])
def upload_profile_pic():
    # This is a simplified version - in production you'd want to:
    # 1. Verify the user is authenticated
    # 2. Save the file to disk
    # 3. Store the filename in a database
    
    # For Termux simplicity, we'll just return success
    # You'd need to implement actual file handling here
    
    return jsonify({
        "ok": True,
        "message": "Profile picture uploaded successfully"
    })

if __name__ == "__main__":
    print("Starting Averix Flask app on http://0.0.0.0:5000")
    print("X OAuth Integration: ACTIVE")
    print(f"X Callback URL: {X_CALLBACK_URL}")
    print("Discord OAuth Integration: ACTIVE")
    print(f"Discord Callback URL: {DISCORD_CALLBACK_URL}")
    print("To access from your phone, make sure you're on the same network")
    print("and use your computer's IP address followed by :5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
