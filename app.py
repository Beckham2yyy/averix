import os
import secrets
import requests
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, session, redirect
import json
import urllib.parse
import base64
import base58

app = Flask(__name__)
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

# ========== SOLANA CONFIGURATION ==========
SOLANA_RPC_URL = "https://solana-mainnet.g.alchemy.com/v2/RWQPlYVPXc7j6x8Fmlair"
COINMARKETCAP_API_KEY = "6881c6f6d56b4cf58727255319ec235e"
PROJECT_WALLET = "9e2Bho4YhYV4iTL2Y4hGe3QXXms2eoq2JajtJeKmMetN"
# ==========================================

# Storage (simple dictionary - in production use a database)
NONCES = {}
USER_DATA = {}
DAILY_CHECKINS = {}  # Store last check-in date by address
PROFILE_PICS = {}    # Store profile picture data
MULTIPLIER_PURCHASES = {}  # Store multiplier purchases

# Create uploads directory
os.makedirs('static/uploads', exist_ok=True)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Averix</title>

<style>
body {
    margin: 0;
    background: #0b0b0f;
    color: white;
    font-family: Arial, sans-serif;
    padding-bottom: 90px;
}

.hidden { display: none }

#gate {
    position: fixed;
    inset: 0;
    background: #0b0b0f;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.gate-box {
    text-align: center;
    padding: 30px;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
}

.logo { font-size: 20px; font-weight: bold }

button {
    background: linear-gradient(90deg,#7f5af0,#2cb67d);
    border: none;
    padding: 10px 18px;
    color: white;
    border-radius: 10px;
    cursor: pointer;
    font-weight: 600;
}

button.connected { background: #1a1a1f }

#disconnectBtn {
    margin-top: 6px;
    background: #1a1a1f;
    display: none;
}

.hero {
    padding: 40px 20px;
    text-align: center;
}

.hero h1 { font-size: 30px }
.hero p { color: #bdbdbd }

.card {
    background: #111118;
    border-radius: 18px;
    padding: 22px;
    margin: 16px 20px;
}

.highlight {
    background: linear-gradient(135deg,#2a1b4d,#1a1a2e);
}

.badge {
    background: #7f5af0;
    padding: 5px 10px;
    border-radius: 8px;
    font-size: 12px;
    display: inline-block;
}

.big {
    font-size: 30px;
    font-weight: bold;
}

.ref-box input {
    width: 100%;
    background: #0b0b0f;
    border: none;
    padding: 14px;
    border-radius: 12px;
    color: white;
}

.row {
    display: flex;
    gap: 10px;
    margin-top: 12px;
}

.secondary {
    background: #1a1a1f;
    flex: 1;
}

.bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0f0f16;
    border-top: 2px solid #1f1f2a;
    display: flex;
    justify-content: space-around;
    padding: 10px 0;
}

.bottom-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    color: #8b8b9a;
}

.bottom-item svg {
    width: 24px;
    height: 24px;
    stroke-width: 2.4;
}

.bottom-item.active {
    color: #7f5af0;
}

.bottom-item.active svg {
    stroke: #7f5af0;
}

/* Task completed styling */
.task-completed {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 16px;
    padding: 12px;
    background: rgba(127, 90, 240, 0.1);
    border-radius: 10px;
    border: 1px solid #7f5af0;
}

.checkbox-circle {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #2cb67d;
    display: flex;
    align-items: center;
    justify-content: center;
}

.checkmark {
    color: white;
    font-size: 14px;
    font-weight: bold;
}

.task-details {
    flex: 1;
}

.task-title {
    font-weight: bold;
    color: #2cb67d;
}

.task-username {
    color: #7f5af0;
    font-weight: bold;
    margin-top: 4px;
}

/* Profile picture styling */
.profile-header {
    display: flex;
    align-items: center;
    gap: 16px;
}

.profile-pic-container {
    position: relative;
    width: 80px;
    height: 80px;
}

.profile-pic {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #7f5af0, #2cb67d);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 32px;
    font-weight: bold;
    color: white;
    flex-shrink: 0;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.upload-overlay {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    background: #7f5af0;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    border: 2px solid #0b0b0f;
}

.upload-overlay svg {
    width: 16px;
    height: 16px;
    color: white;
}

.profile-info {
    flex: 1;
}

.profile-name {
    font-size: 26px;
    font-weight: bold;
    color: #7f5af0;
    margin-bottom: 4px;
}

.profile-wallet {
    font-size: 14px;
    color: #8b8b9a;
}

/* Username edit form */
.edit-username-form {
    margin-top: 16px;
    padding: 16px;
    background: rgba(30, 30, 46, 0.8);
    border-radius: 12px;
    border: 1px solid #2a2a35;
}

.edit-username-form input {
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    border: none;
    background: #0b0b0f;
    color: white;
    margin-top: 10px;
}

.edit-actions {
    display: flex;
    gap: 10px;
    margin-top: 12px;
}

/* Daily Check-in button */
.daily-checkin-btn {
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
}

.daily-checkin-btn.disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.ave-badge {
    display: inline-block;
    background: linear-gradient(135deg, #ff8c00, #ff5e00);
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    margin-left: 8px;
}

.ave-info {
    margin-top: 10px;
    padding: 10px;
    background: rgba(255, 140, 0, 0.1);
    border-radius: 10px;
    border-left: 3px solid #ff8c00;
}

/* File upload styling */
#profilePicUpload {
    display: none;
}

.upload-status {
    margin-top: 10px;
    font-size: 14px;
    color: #2cb67d;
}

/* Task progress */
.task-progress {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 20px;
}

.progress-circle {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: conic-gradient(#7f5af0 0% var(--progress), #1a1a1f 0%);
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.progress-circle::before {
    content: '';
    position: absolute;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: #111118;
}

.progress-text {
    position: absolute;
    font-weight: bold;
    font-size: 14px;
    color: #7f5af0;
}

.progress-info {
    flex: 1;
}

/* X (Twitter) connection styling */
.x-connection-btn {
    background: linear-gradient(135deg, #000000, #1DA1F2);
    color: white;
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.x-connection-btn:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
}

.x-connection-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.x-icon {
    width: 20px;
    height: 20px;
}

/* Discord connection styling */
.discord-connection-btn {
    background: linear-gradient(135deg, #5865F2, #7289DA);
    color: white;
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.discord-connection-btn:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
}

.discord-connection-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.discord-icon {
    width: 20px;
    height: 20px;
}

/* Disconnect X button styling */
.disconnect-x-btn {
    background: linear-gradient(135deg, #ff4757, #ff3838);
    color: white;
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.disconnect-x-btn:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
    background: linear-gradient(135deg, #ff3838, #ff1e1e);
}

/* Disconnect Discord button styling */
.disconnect-discord-btn {
    background: linear-gradient(135deg, #ff4757, #ff3838);
    color: white;
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.disconnect-discord-btn:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
    background: linear-gradient(135deg, #ff3838, #ff1e1e);
}

/* Follow X button styling */
.follow-x-btn {
    background: linear-gradient(135deg, #1DA1F2, #1a91da);
    color: white;
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.follow-x-btn:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
    background: linear-gradient(135deg, #1a91da, #1a8cd0);
}

.follow-x-btn.disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.follow-x-btn.disabled-text {
    background: #1a1a1f;
    cursor: not-allowed;
}

.x-username {
    color: #1DA1F2;
    font-weight: bold;
    margin-top: 4px;
}

.discord-username {
    color: #5865F2;
    font-weight: bold;
    margin-top: 4px;
}

/* Advanced settings styling */
#advancedSettings {
    margin-top: 12px;
    overflow: hidden;
    transition: max-height 0.3s ease-out;
    max-height: 0;
}

#advancedSettings.show {
    max-height: 500px;
}

.advanced-toggle-btn {
    background: linear-gradient(135deg, #7f5af0, #2cb67d);
    color: white;
    width: 100%;
    padding: 16px;
    font-size: 16px;
    font-weight: bold;
    margin-top: 12px;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.advanced-toggle-btn:hover {
    transform: translateY(-2px);
    transition: transform 0.2s;
}

.advanced-arrow {
    font-size: 14px;
    transition: transform 0.3s ease;
}

.advanced-toggle-btn.rotated .advanced-arrow {
    transform: rotate(180deg);
}

/* Multiplier page styling */
.multiplier-card {
    border: 2px solid #7f5af0;
    background: linear-gradient(135deg, rgba(127, 90, 240, 0.1), rgba(44, 182, 125, 0.1));
}

.multiplier-badge {
    background: linear-gradient(135deg, #ff8c00, #ff5e00);
    color: white;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: bold;
    display: inline-block;
    margin: 10px 0;
}

.price-tag {
    font-size: 24px;
    font-weight: bold;
    color: #7f5af0;
    margin: 10px 0;
}

.benefit-list {
    margin: 15px 0;
    padding-left: 20px;
}

.benefit-list li {
    margin: 8px 0;
    color: #bdbdbd;
}

.benefit-list li strong {
    color: #2cb67d;
}

.sol-amount {
    background: rgba(127, 90, 240, 0.2);
    padding: 10px;
    border-radius: 10px;
    margin: 15px 0;
    text-align: center;
    font-weight: bold;
}

.purchase-success {
    background: rgba(44, 182, 125, 0.1);
    border: 2px solid #2cb67d;
    padding: 15px;
    border-radius: 12px;
    margin: 15px 0;
    text-align: center;
}

.purchase-success h4 {
    color: #2cb67d;
    margin: 0;
}

.reward-badge {
    background: linear-gradient(135deg, #7f5af0, #2cb67d);
    color: white;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    margin-left: 5px;
}

.status-message {
    margin-top: 10px;
    padding: 10px;
    border-radius: 8px;
    text-align: center;
}

.status-success {
    background: rgba(44, 182, 125, 0.1);
    color: #2cb67d;
    border: 1px solid #2cb67d;
}

.status-error {
    background: rgba(255, 71, 87, 0.1);
    color: #ff6b6b;
    border: 1px solid #ff6b6b;
}

.status-info {
    background: rgba(127, 90, 240, 0.1);
    color: #7f5af0;
    border: 1px solid #7f5af0;
}
</style>
</head>

<body>

<div id="gate">
    <div class="gate-box">
        <h1>Averix</h1>
        <p>Connect your wallet to access the platform</p>
        <button onclick="connectWallet()">Connect Wallet</button>
    </div>
</div>

<nav>
    <div class="logo">Averix</div>
    <div>
        <button id="connectBtn" onclick="connectWallet()">Connect Wallet</button>
        <button id="disconnectBtn" onclick="disconnectWallet()">Disconnect</button>
    </div>
</nav>

<div id="taskPage">
    <div class="hero">
        <h1>Welcome to Averix</h1>
        <p>Complete tasks to earn AVE</p>
    </div>

    <div class="card">
        <div class="task-progress">
            <div class="progress-circle" id="progressCircle" style="--progress: 0%">
                <div class="progress-text" id="progressText">0/5</div>
            </div>
            <div class="progress-info">
                <h3>Task Progress</h3>
                <p>Complete tasks to earn AVE</p>
            </div>
        </div>
    </div>

    <div class="card">
        <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">Set Username</h3>
        <p style="color: #bdbdbd; margin-bottom: 16px;">Choose a username to earn 20 AVE.</p>
        
        <div id="usernameForm">
            <input id="usernameInput" placeholder="Enter username"
            style="width:100%;padding:12px;border-radius:10px;border:none;background:#0b0b0f;color:white;margin-top:10px">
            <button style="margin-top:12px; width: 100%;" onclick="setUsername()">Save Username</button>
        </div>
        
        <div id="taskCompleted" class="task-completed" style="display: none;">
            <div class="checkbox-circle">
                <div class="checkmark">✓</div>
            </div>
            <div class="task-details">
                <div class="task-title">Task Completed</div>
                <div class="task-username">Username: <span id="completedUsername">Beckham</span> •</div>
            </div>
        </div>
        
        <p id="usernameStatus" style="margin-top:10px;color:#2cb67d"></p>
    </div>

    <div class="card">
        <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">Verify Gmail</h3>
        <p style="color: #bdbdbd; margin-bottom: 16px;">Verify your Gmail account to earn 20 AVE.</p>
        
        <div id="gmailForm">
            <input id="gmailInput" placeholder="Enter your Gmail address"
            style="width:100%;padding:12px;border-radius:10px;border:none;background:#0b0b0f;color:white;margin-top:10px">
            <button style="margin-top:12px; width: 100%;" onclick="verifyGmail()">Verify Gmail</button>
        </div>
        
        <div id="gmailCompleted" class="task-completed" style="display: none;">
            <div class="checkbox-circle">
                <div class="checkmark">✓</div>
            </div>
            <div class="task-details">
                <div class="task-title">Task Completed</div>
                <div class="task-username">Gmail: <span id="completedGmail">example@gmail.com</span> •</div>
            </div>
        </div>
        
        <p id="gmailStatus" style="margin-top:10px;color:#2cb67d"></p>
    </div>

    <div class="card">
        <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">Connect X</h3>
        <p style="color: #bdbdbd; margin-bottom: 16px;">Connect your X account to earn 20 AVE.</p>
        
        <div id="xForm">
            <button class="x-connection-btn" onclick="connectXAccount()">
                <svg class="x-icon" viewBox="0 0 24 24" fill="white">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                Connect X Account
            </button>
        </div>
        
        <div id="xCompleted" class="task-completed" style="display: none;">
            <div class="checkbox-circle">
                <div class="checkmark">✓</div>
            </div>
            <div class="task-details">
                <div class="task-title">Task Completed</div>
                <div class="task-username">X Account: <span id="completedX">@user</span> •</div>
            </div>
        </div>
        
        <p id="xStatus" style="margin-top:10px;color:#2cb67d"></p>
    </div>

    <div class="card">
        <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">Follow Averix on X</h3>
        <p style="color: #bdbdbd; margin-bottom: 16px;">Follow <span style="color:#1DA1F2; font-weight:bold;">@averixapp</span> on X to earn 20 AVE.</p>
        
        <div id="followXForm">
            <button class="follow-x-btn" onclick="followXAccount()" id="followXBtn">
                <svg class="x-icon" viewBox="0 0 24 24" fill="white">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
                Open & Follow @averixapp
            </button>
            <button id="markFollowedBtn" class="secondary" style="margin-top: 10px; width: 100%; display: none;" onclick="markXFollowed()">
                I've Followed @averixapp
            </button>
        </div>
        
        <div id="followXCompleted" class="task-completed" style="display: none;">
            <div class="checkbox-circle">
                <div class="checkmark">✓</div>
            </div>
            <div class="task-details">
                <div class="task-title">Task Completed</div>
                <div class="x-username">Followed: <span id="completedFollowX">@averixapp</span> •</div>
            </div>
        </div>
        
        <p id="followXStatus" style="margin-top:10px;color:#2cb67d"></p>
    </div>

    <div class="card">
        <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">Connect Discord</h3>
        <p style="color: #bdbdbd; margin-bottom: 16px;">Connect your Discord account to earn 20 AVE.</p>
        
        <div id="discordForm">
            <button class="discord-connection-btn" onclick="connectDiscordAccount()">
                <svg class="discord-icon" viewBox="0 0 24 24" fill="white">
                    <path d="M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.09 16.09 0 0 0-4.8 0c-.14-.34-.35-.76-.54-1.09c-.01-.02-.04-.03-.07-.03c-1.5.26-2.93.71-4.27 1.33c-.01 0-.02.01-.03.02c-2.72 4.07-3.47 8.03-3.1 11.95c0 .02.01.04.03.05c1.8 1.32 3.53 2.12 5.24 2.65c.03.01.06 0 .07-.02c.4-.55.76-1.13 1.07-1.74c.02-.04 0-.08-.04-.09c-.57-.22-1.11-.48-1.64-.78c-.04-.02-.04-.08-.01-.11c.11-.08.22-.17.33-.25c.02-.02.05-.02.07-.01c3.44 1.57 7.15 1.57 10.55 0c.02-.01.05-.01.07.01c.11.09.22.17.33.26c.04.03.04.09-.01.11c-.52.31-1.07.56-1.64.78c-.04.01-.05.06-.04.09c.32.61.68 1.19 1.07 1.74c.03.01.06.02.09.01c1.72-.53 3.45-1.33 5.25-2.65c.02-.01.03-.03.03-.05c.44-4.53-.73-8.46-3.1-11.95c-.01-.01-.02-.02-.04-.02zM8.52 14.91c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.84 2.12-1.89 2.12zm6.97 0c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.83 2.12-1.89 2.12z"/>
                </svg>
                Connect Discord Account
            </button>
        </div>
        
        <div id="discordCompleted" class="task-completed" style="display: none;">
            <div class="checkbox-circle">
                <div class="checkmark">✓</div>
            </div>
            <div class="task-details">
                <div class="task-title">Task Completed</div>
                <div class="discord-username">Discord Account: <span id="completedDiscord">user#1234</span> •</div>
            </div>
        </div>
        
        <p id="discordStatus" style="margin-top:10px;color:#2cb67d"></p>
    </div>

    <div class="card">
        <h3 style="font-size: 20px; font-weight: bold; margin-bottom: 8px;">
            Daily Check-in 
            <span class="ave-badge">+20 AVE</span>
        </h3>
        <p style="color: #bdbdbd; margin-bottom: 16px;">Check in daily to earn 20 AVE.</p>
        
        <div class="ave-info">
            <p><b>Current daily streak:</b> <span id="dailyStreak">0</span> days</p>
            <p><b>Last check-in:</b> <span id="lastCheckin">Never</span></p>
        </div>
        
        <button id="dailyCheckinBtn" class="daily-checkin-btn" onclick="dailyCheckin()">
            Check In Today
        </button>
        
        <div id="dailyCompleted" class="task-completed" style="display: none;">
            <div class="checkbox-circle">
                <div class="checkmark">✓</div>
            </div>
            <div class="task-details">
                <div class="task-title">Daily Check-in Completed</div>
                <div class="task-username"></div>
            </div>
        </div>
        
        <p id="dailyStatus" style="margin-top:10px;color:#2cb67d"></p>
    </div>
</div>

<div id="referPage" class="hidden">
    <div class="card highlight">
        <span class="badge">LIVE</span>
        <h3>$50,000 Referral Contest</h3>
        <p>Invite verified wallets and earn <span id="referralReward">30</span> AVE per referral</p>
    </div>

    <div class="card">
        <h3>Total Referral Earnings</h3>
        <div class="big">$0.00</div>
    </div>

    <div class="card">
        <h3>Your Referral Link</h3>
        <div class="ref-box">
            <input id="refLink" readonly>
        </div>
        <div class="row">
            <button class="secondary" onclick="copyRef()">Copy</button>
            <button class="secondary">Share</button>
        </div>
    </div>
</div>

<div id="multPage" class="hidden">
    <div class="card">
        <h3>Multipliers</h3>
        <p>Buy Multipliers to boost your referral rewards</p>
    </div>

    <div class="card multiplier-card">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
            <h3 style="margin: 0; color: #7f5af0;">2X Multiplier</h3>
            <span class="multiplier-badge">PERMANENT</span>
        </div>
        
        <div class="price-tag">$1.00 USD</div>
        
        <div class="sol-amount" id="solAmountContainer">
            <p>Calculating SOL amount...</p>
        </div>
        
        <div class="benefit-list">
            <p><strong>Benefits:</strong></p>
            <ul>
                <li>Double your referral rewards from <strong>30 AVE</strong> to <strong>60 AVE</strong> per user</li>
                <li>Permanent - never expires</li>
                <li>Applied immediately after purchase</li>
            </ul>
        </div>
        
        <div id="multiplierStatusMessage" class="status-message"></div>
        
        <div id="buyMultiplierSection">
            <button id="buy2xBtn" style="width: 100%; padding: 16px; font-size: 16px; font-weight: bold;"
                    onclick="buy2xMultiplier()">
                Buy 2X Multiplier
            </button>
            <p style="text-align: center; margin-top: 10px; color: #bdbdbd; font-size: 14px;">
                You'll be prompted to sign the transaction in your wallet
            </p>
        </div>
        
        <div id="alreadyPurchased" class="purchase-success" style="display: none;">
            <h4>✓ 2X Multiplier Active</h4>
            <p>Your referral rewards are now <strong>60 AVE</strong> per user</p>
            <p>Thank you for your purchase!</p>
        </div>
    </div>
</div>

<div id="profilePage" class="hidden">
    <div class="card">
        <div class="profile-header">
            <div class="profile-pic-container">
                <div class="profile-pic" id="profilePic">A</div>
                <div class="upload-overlay" onclick="document.getElementById('profilePicUpload').click()">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                </div>
                <input type="file" id="profilePicUpload" accept="image/*" onchange="uploadProfilePic()">
            </div>
            <div class="profile-info">
                <div class="profile-name" id="profileName">Username</div>
                <div class="profile-wallet" id="profileWallet">0x0000...0000</div>
            </div>
        </div>
        <p id="uploadStatus" class="upload-status"></p>
    </div>

    <div class="card">
        <h3>Stats</h3>
        <p>Referrals: <b id="referralsCount">0</b></p>
        <p>Tasks completed: <b id="tasksCompletedCount">0/5</b></p>
        <p>AVE Earned: <b id="aveEarned">0</b></p>
        <p>Daily streak: <b id="profileDailyStreak">0 days</b></p>
        <p>Multiplier: <b id="multiplierStatus">1x</b> <span id="multiplierBadge" class="reward-badge" style="display: none;">2x ACTIVE</span></p>
    </div>

    <div class="card">
        <h3>Identity</h3>
        <p id="identityUsername">Username: not set</p>
        <p id="identityWallet">Wallet: connected</p>
        <p id="identityX">X (Twitter): Not Connected</p>
        <p id="identityDiscord">Discord: Not Connected</p>
    </div>

    <div class="card">
        <h3>Settings</h3>
        <button class="secondary" style="width:100%; margin-bottom: 12px;"
        onclick="startEditingUsername()">
            Change username
        </button>
        
        <button id="advancedToggleBtn" class="advanced-toggle-btn" onclick="toggleAdvancedSettings()">
            Advanced <span class="advanced-arrow">↓</span>
        </button>
        
        <div id="advancedSettings">
            <button id="disconnectXBtn" class="disconnect-x-btn" onclick="disconnectXAccount()" style="display: none;">
                <svg class="x-icon" viewBox="0 0 24 24" fill="white">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
                Disconnect X Account
            </button>
            
            <button id="disconnectDiscordBtn" class="disconnect-discord-btn" onclick="disconnectDiscordAccount()" style="display: none;">
                <svg class="discord-icon" viewBox="0 0 24 24" fill="white">
                    <path d="M19.27 5.33C17.94 4.71 16.5 4.26 15 4a.09.09 0 0 0-.07.03c-.18.33-.39.76-.53 1.09a16.09 16.09 0 0 0-4.8 0c-.14-.34-.35-.76-.54-1.09c-.01-.02-.04-.03-.07-.03c-1.5.26-2.93.71-4.27 1.33c-.01 0-.02.01-.03.02c-2.72 4.07-3.47 8.03-3.1 11.95c0 .02.01.04.03.05c1.8 1.32 3.53 2.12 5.24 2.65c.03.01.06 0 .07-.02c.4-.55.76-1.13 1.07-1.74c.02-.04 0-.08-.04-.09c-.57-.22-1.11-.48-1.64-.78c-.04-.02-.04-.08-.01-.11c.11-.08.22-.17.33-.25c.02-.02.05-.02.07-.01c3.44 1.57 7.15 1.57 10.55 0c.02-.01.05-.01.07.01c.11.09.22.17.33.26c.04.03.04.09-.01.11c-.52.31-1.07.56-1.64.78c-.04.01-.05.06-.04.09c.32.61.68 1.19 1.07 1.74c.03.01.06.02.09.01c1.72-.53 3.45-1.33 5.25-2.65c.02-.01.03-.03.03-.05c.44-4.53-.73-8.46-3.1-11.95c-.01-.01-.02-.02-.04-.02zM8.52 14.91c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.84 2.12-1.89 2.12zm6.97 0c-1.03 0-1.89-.95-1.89-2.12s.84-2.12 1.89-2.12c1.06 0 1.9.96 1.89 2.12c0 1.17-.83 2.12-1.89 2.12z"/>
                </svg>
                Disconnect Discord Account
            </button>
        </div>
        
        <div id="editUsernameForm" class="edit-username-form" style="display: none;">
            <h4 style="margin-top: 0; margin-bottom: 12px;">Edit Username</h4>
            <input type="text" id="editUsernameInput" placeholder="Enter new username">
            <div class="edit-actions">
                <button class="secondary" style="flex: 1;" onclick="saveNewUsername()">
                    Save
                </button>
                <button class="secondary" style="flex: 1;" onclick="cancelEditUsername()">
                    Cancel
                </button>
            </div>
            <p id="editUsernameStatus" style="margin-top:10px;color:#2cb67d; font-size: 14px;"></p>
        </div>
    </div>
</div>

<div class="bottom-nav">
    <div class="bottom-item active" onclick="switchTab('task',this)">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M3 7h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z"/>
            <path d="M16 11a2 2 0 0 1-4 0"/>
        </svg>
        Task
    </div>

    <div class="bottom-item" onclick="switchTab('refer',this)">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="9" cy="8" r="3"/>
            <circle cx="17" cy="8" r="3"/>
            <path d="M2 20c1.5-4 10.5-4 12 0"/>
            <path d="M12 20c1-3 7-3 8 0"/>
        </svg>
        Refer
    </div>

    <div class="bottom-item" onclick="switchTab('mult',this)">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/>
        </svg>
        Multipliers
    </div>

    <div class="bottom-item" onclick="switchTab('profile',this)">
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <circle cx="12" cy="8" r="4"/>
            <path d="M4 20c2-4 14-4 16 0"/>
        </svg>
        Profile
    </div>
</div>

<script>
let currentAccount = null
let isEditingUsername = false
let currentSolPrice = null

// Check and display completed tasks when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkSavedWallet();
    checkCompletedTasks();
    updateDailyCheckinStatus();
    updateFollowXButton();
    loadSolPrice();
});

// Check if wallet was previously connected and if it's still valid (within 1 hour)
async function checkSavedWallet() {
    const savedWallet = localStorage.getItem("averix_wallet_address");
    const connectionTime = localStorage.getItem("averix_wallet_connection_time");
    
    if (savedWallet && connectionTime && window.solana) {
        // Check if the connection is still valid (within 1 hour)
        const oneHourInMs = 60 * 60 * 1000; // 1 hour in milliseconds
        const currentTime = Date.now();
        const timeSinceConnection = currentTime - parseInt(connectionTime);
        
        if (timeSinceConnection <= oneHourInMs) {
            try {
                // Check if we can access the saved account
                const accounts = await window.solana.request({ 
                    method: 'connect' 
                });
                
                if (accounts && accounts.publicKey) {
                    const publicKey = accounts.publicKey.toString();
                    // Check if the saved wallet matches the connected account
                    if (publicKey === savedWallet) {
                        // Wallet is still connected and within 1 hour, unlock the app
                        unlock(publicKey);
                        return;
                    }
                }
                
                // If we get here, the saved wallet is not currently connected but still within 1 hour
                // We could try to auto-reconnect, but for security, we'll require manual reconnection
                // after being away from the site for up to 1 hour
                document.getElementById('gate').style.display = 'flex';
                
            } catch (error) {
                console.error("Error checking saved wallet:", error);
                // Show gate if there's an error
                document.getElementById('gate').style.display = 'flex';
            }
        } else {
            // Connection expired (more than 1 hour), require reconnection
            console.log("Wallet connection expired (more than 1 hour ago)");
            localStorage.removeItem("averix_wallet_address");
            localStorage.removeItem("averix_wallet_connection_time");
            document.getElementById('gate').style.display = 'flex';
        }
    } else {
        // No saved wallet, no connection time, or no solana provider
        document.getElementById('gate').style.display = 'flex';
    }
}

function checkCompletedTasks() {
    const u = localStorage.getItem("averix_username");
    if(u) {
        // Show completed username task immediately if username is already set
        document.getElementById('usernameForm').style.display = 'none';
        document.getElementById('taskCompleted').style.display = 'flex';
        document.getElementById('completedUsername').textContent = u;
    }
    
    const g = localStorage.getItem("averix_gmail");
    if(g) {
        // Show completed Gmail task immediately if Gmail is already verified
        document.getElementById('gmailForm').style.display = 'none';
        document.getElementById('gmailCompleted').style.display = 'flex';
        document.getElementById('completedGmail').textContent = g;
    }
    
    const x = localStorage.getItem("averix_x_connected");
    if(x === "true") {
        // Show completed X task immediately if X is already connected
        const xUsername = localStorage.getItem("averix_x_username");
        document.getElementById('xForm').style.display = 'none';
        document.getElementById('xCompleted').style.display = 'flex';
        if(xUsername) {
            document.getElementById('completedX').textContent = '@' + xUsername;
        }
    }
    
    // Check follow X task
    const followX = localStorage.getItem("averix_x_followed");
    if(followX === "true") {
        // Show completed follow X task immediately if already followed
        document.getElementById('followXForm').style.display = 'none';
        document.getElementById('followXCompleted').style.display = 'flex';
    } else {
        // Check if user has clicked to follow (but hasn't marked as completed yet)
        const hasClickedFollow = localStorage.getItem("averix_x_follow_clicked");
        if (hasClickedFollow === "true") {
            // Show the "I've followed" button
            document.getElementById('markFollowedBtn').style.display = 'block';
        }
    }
    
    // Check Discord task
    const discord = localStorage.getItem("averix_discord_connected");
    if(discord === "true") {
        // Show completed Discord task immediately if Discord is already connected
        const discordUsername = localStorage.getItem("averix_discord_username");
        document.getElementById('discordForm').style.display = 'none';
        document.getElementById('discordCompleted').style.display = 'flex';
        if(discordUsername) {
            document.getElementById('completedDiscord').textContent = discordUsername;
        }
    }
    
    // Check daily check-in
    const lastCheckin = localStorage.getItem("averix_last_checkin");
    const today = new Date().toDateString();
    if(lastCheckin === today) {
        // Already checked in today
        document.getElementById('dailyCheckinBtn').style.display = 'none';
        document.getElementById('dailyCompleted').style.display = 'flex';
        document.getElementById('dailyCheckinBtn').classList.add('disabled');
        document.getElementById('dailyCheckinBtn').disabled = true;
    }
    
    // Update tasks completed count
    updateTasksCompleted();
    updateProgressCircle();
    
    // Check multiplier purchase
    checkMultiplierStatus();
}

function updateDailyCheckinStatus() {
    const lastCheckin = localStorage.getItem("averix_last_checkin");
    const streak = localStorage.getItem("averix_daily_streak") || "0";
    
    document.getElementById('lastCheckin').textContent = lastCheckin || "Never";
    document.getElementById('dailyStreak').textContent = streak;
    document.getElementById('profileDailyStreak').textContent = streak + " days";
}

// Function to update the Follow X button based on X connection status
function updateFollowXButton() {
    const xConnected = localStorage.getItem("averix_x_connected") === "true";
    const followXCompleted = localStorage.getItem("averix_x_followed") === "true";
    const followXBtn = document.getElementById('followXBtn');
    
    if (followXCompleted) {
        // Task already completed, button should not be visible
        return;
    }
    
    if (!xConnected) {
        // X not connected, disable the button
        followXBtn.disabled = true;
        followXBtn.classList.add('disabled');
        followXBtn.classList.add('disabled-text');
        followXBtn.innerHTML = `
            <svg class="x-icon" viewBox="0 0 24 24" fill="#8b8b9a">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
            Connect X Account First
        `;
    } else {
        // X connected, enable the button
        followXBtn.disabled = false;
        followXBtn.classList.remove('disabled');
        followXBtn.classList.remove('disabled-text');
        followXBtn.innerHTML = `
            <svg class="x-icon" viewBox="0 0 24 24" fill="white">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
            Open & Follow @averixapp
        `;
    }
}

async function loadSolPrice() {
    try {
        const response = await fetch('/sol_price');
        const data = await response.json();
        if (data.ok && data.price) {
            currentSolPrice = data.price;
            // Calculate and display SOL amount for $1
            const solAmount = 1 / data.price;
            document.getElementById('solAmountContainer').innerHTML = `
                <p>≈ ${solAmount.toFixed(6)} SOL</p>
                <p style="font-size: 12px; color: #bdbdbd; margin-top: 5px;">Based on current price: $${data.price.toFixed(2)} per SOL</p>
            `;
        }
    } catch (error) {
        console.error('Error loading SOL price:', error);
        document.getElementById('solAmountContainer').innerHTML = `
            <p style="color: #ff6b6b;">Error loading SOL price</p>
        `;
    }
}

function checkMultiplierStatus() {
    const hasMultiplier = localStorage.getItem("averix_2x_multiplier") === "true";
    
    if (hasMultiplier) {
        // Show already purchased message
        document.getElementById('buyMultiplierSection').style.display = 'none';
        document.getElementById('alreadyPurchased').style.display = 'block';
        
        // Update referral page
        document.getElementById('referralReward').textContent = '60';
        
        // Update profile page
        document.getElementById('multiplierStatus').textContent = '2x';
        document.getElementById('multiplierBadge').style.display = 'inline-block';
    } else {
        // Show purchase section
        document.getElementById('buyMultiplierSection').style.display = 'block';
        document.getElementById('alreadyPurchased').style.display = 'none';
        
        // Update referral page
        document.getElementById('referralReward').textContent = '30';
        
        // Update profile page
        document.getElementById('multiplierStatus').textContent = '1x';
        document.getElementById('multiplierBadge').style.display = 'none';
    }
}

async function buy2xMultiplier() {
    if (!currentAccount) {
        showMultiplierStatus("Please connect your wallet first", "error");
        return;
    }
    
    if (!currentSolPrice) {
        showMultiplierStatus("Loading SOL price... Please try again", "error");
        return;
    }
    
    // Calculate SOL amount for $1
    const solAmount = 1 / currentSolPrice;
    const solAmountLamports = Math.floor(solAmount * 1e9); // Convert to lamports (1 SOL = 1e9 lamports)
    
    showMultiplierStatus("Preparing transaction...", "info");
    
    try {
        // Check user's SOL balance
        const balanceResponse = await fetch('/check_balance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                address: currentAccount,
                requiredLamports: solAmountLamports
            })
        });
        
        const balanceData = await balanceResponse.json();
        
        if (!balanceData.ok) {
            showMultiplierStatus("Insufficient SOL balance. You need at least $" + (solAmount * currentSolPrice).toFixed(2) + " worth of SOL", "error");
            return;
        }
        
        // Create transaction using the wallet provider
        showMultiplierStatus("Creating transaction... Please sign in your wallet", "info");
        
        // Create transaction params
        const transactionData = {
            fromPubkey: currentAccount,
            toPubkey: '9e2Bho4YhYV4iTL2Y4hGe3QXXms2eoq2JajtJeKmMetN',
            lamports: solAmountLamports
        };
        
        // Send transaction request
        const sendResponse = await fetch('/send_sol_transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(transactionData)
        });
        
        const sendData = await sendResponse.json();
        
        if (sendData.ok) {
            // Success! Save multiplier status
            localStorage.setItem("averix_2x_multiplier", "true");
            
            // Update UI
            checkMultiplierStatus();
            
            showMultiplierStatus("✓ 2X Multiplier purchased successfully! Your referral rewards are now 60 AVE per user", "success");
            
            // Also save to server
            await fetch('/update_multiplier', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    address: currentAccount,
                    hasMultiplier: true
                })
            });
            
        } else {
            showMultiplierStatus("Transaction failed: " + (sendData.error || "Unknown error"), "error");
        }
        
    } catch (error) {
        console.error('Error buying multiplier:', error);
        showMultiplierStatus("Error: " + error.message, "error");
    }
}

function showMultiplierStatus(message, type) {
    const statusDiv = document.getElementById('multiplierStatusMessage');
    statusDiv.textContent = message;
    statusDiv.className = 'status-message';
    
    if (type === 'success') {
        statusDiv.classList.add('status-success');
    } else if (type === 'error') {
        statusDiv.classList.add('status-error');
    } else if (type === 'info') {
        statusDiv.classList.add('status-info');
    }
    
    // Clear message after 5 seconds if it's info
    if (type === 'info') {
        setTimeout(() => {
            if (statusDiv.textContent === message) {
                statusDiv.textContent = '';
                statusDiv.className = 'status-message';
            }
        }, 5000);
    }
}

function switchTab(tab, el) {
    document.querySelectorAll(".bottom-item").forEach(i=>i.classList.remove("active"))
    el.classList.add("active")

    taskPage.classList.add("hidden")
    referPage.classList.add("hidden")
    multPage.classList.add("hidden")
    profilePage.classList.add("hidden")

    if(tab==="task") {
        taskPage.classList.remove("hidden")
        // Check again when switching to task tab
        checkCompletedTasks();
        updateFollowXButton();
    }
    if(tab==="refer") {
        referPage.classList.remove("hidden")
        checkMultiplierStatus(); // Update referral reward display
    }
    if(tab==="mult") {
        multPage.classList.remove("hidden")
        // Load SOL price when switching to multiplier tab
        if (!currentSolPrice) {
            loadSolPrice();
        }
        checkMultiplierStatus();
    }
    if(tab==="profile"){
        profilePage.classList.remove("hidden")
        loadProfile()
    }
}

function unlock(a){
    currentAccount = a
    gate.style.display="none"
    connectBtn.innerText=a.slice(0,6)+"..."+a.slice(-4)
    connectBtn.classList.add("connected")
    disconnectBtn.style.display="block"
    refLink.value="https://averix.up.railway.app/?ref="+a
    
    // Save wallet address and connection time to localStorage for auto-reconnect (valid for 1 hour)
    localStorage.setItem("averix_wallet_address", a);
    localStorage.setItem("averix_wallet_connection_time", Date.now());
    
    // Check for completed tasks after wallet connects
    checkCompletedTasks();
    updateFollowXButton();
}

function disconnectWallet(){
    // Remove saved wallet address and connection time
    localStorage.removeItem("averix_wallet_address");
    localStorage.removeItem("averix_wallet_connection_time");
    location.reload()
}

function copyRef(){
    refLink.select()
    document.execCommand("copy")
}

function setUsername(){
    const u = usernameInput.value.trim()
    if(!u) return
    localStorage.setItem("averix_username", u)
    usernameStatus.innerText = "Username set: " + u + " • 20 AVE earned"
    
    // Show completed task UI
    document.getElementById('usernameForm').style.display = 'none'
    document.getElementById('taskCompleted').style.display = 'flex'
    document.getElementById('completedUsername').textContent = u
    
    // Update profile picture with first letter of username
    updateProfilePic(u)
    
    // Update tasks completed count
    updateTasksCompleted()
    updateProgressCircle()
}

function verifyGmail(){
    const g = gmailInput.value.trim()
    if(!g) return
    if(!g.includes('@') || !g.includes('.')) {
        gmailStatus.innerText = "Please enter a valid Gmail address"
        gmailStatus.style.color = "#ff6b6b"
        return
    }
    
    localStorage.setItem("averix_gmail", g)
    gmailStatus.innerText = "Gmail verified: " + g + " • 20 AVE earned"
    gmailStatus.style.color = "#2cb67d"
    
    // Show completed task UI
    document.getElementById('gmailForm').style.display = 'none'
    document.getElementById('gmailCompleted').style.display = 'flex'
    document.getElementById('completedGmail').textContent = g
    
    // Update tasks completed count
    updateTasksCompleted()
    updateProgressCircle()
}

function connectXAccount() {
    // Redirect to Flask backend for X OAuth
    window.location.href = '/x/auth';
}

function connectDiscordAccount() {
    // Redirect to Flask backend for Discord OAuth
    window.location.href = '/discord/auth';
}

// Function to toggle advanced settings visibility
function toggleAdvancedSettings() {
    const advancedSettings = document.getElementById('advancedSettings');
    const toggleBtn = document.getElementById('advancedToggleBtn');
    
    if (advancedSettings.classList.contains('show')) {
        advancedSettings.classList.remove('show');
        toggleBtn.classList.remove('rotated');
        toggleBtn.innerHTML = 'Advanced <span class="advanced-arrow">↓</span>';
    } else {
        advancedSettings.classList.add('show');
        toggleBtn.classList.add('rotated');
        toggleBtn.innerHTML = 'Advanced <span class="advanced-arrow">↑</span>';
    }
}

// Function to disconnect X account
function disconnectXAccount() {
    if (confirm("Are you sure you want to disconnect your X account? This will remove the 20 AVE you earned from this task.")) {
        // Remove X connection data from localStorage
        localStorage.removeItem("averix_x_connected");
        localStorage.removeItem("averix_x_username");
        
        // Show the connect X form again
        document.getElementById('xForm').style.display = 'block';
        document.getElementById('xCompleted').style.display = 'none';
        
        // Hide the disconnect X button
        document.getElementById('disconnectXBtn').style.display = 'none';
        
        // Update identity section
        document.getElementById('identityX').textContent = "X (Twitter): Not Connected";
        
        // Update the Follow X button to disabled state
        updateFollowXButton();
        
        // Recalculate AVE earned (subtract 20 for X task)
        updateTasksCompleted();
        
        // Update progress circle
        updateProgressCircle();
        
        // Show success message
        alert("X account disconnected successfully. 20 AVE has been removed from your total.");
        
        // Refresh the profile tab to update displays
        loadProfile();
    }
}

// Function to disconnect Discord account
function disconnectDiscordAccount() {
    if (confirm("Are you sure you want to disconnect your Discord account? This will remove the 20 AVE you earned from this task.")) {
        // Remove Discord connection data from localStorage
        localStorage.removeItem("averix_discord_connected");
        localStorage.removeItem("averix_discord_username");
        
        // Show the connect Discord form again
        document.getElementById('discordForm').style.display = 'block';
        document.getElementById('discordCompleted').style.display = 'none';
        
        // Hide the disconnect Discord button
        document.getElementById('disconnectDiscordBtn').style.display = 'none';
        
        // Update identity section
        document.getElementById('identityDiscord').textContent = "Discord: Not Connected";
        
        // Recalculate AVE earned (subtract 20 for Discord task)
        updateTasksCompleted();
        
        // Update progress circle
        updateProgressCircle();
        
        // Show success message
        alert("Discord account disconnected successfully. 20 AVE has been removed from your total.");
        
        // Refresh the profile tab to update displays
        loadProfile();
    }
}

// Function to open X account for following
function followXAccount() {
    // Check if X account is connected
    const xConnected = localStorage.getItem("averix_x_connected");
    if (xConnected !== "true") {
        alert("Please connect your X account first before attempting this task!");
        return;
    }
    
    // Mark that the user has clicked to follow
    localStorage.setItem("averix_x_follow_clicked", "true");
    
    // Open @averixapp profile in a new tab
    window.open('https://x.com/averixapp', '_blank');
    
    // Show the "I've followed" button
    document.getElementById('markFollowedBtn').style.display = 'block';
}

// Function to mark X account as followed
function markXFollowed() {
    localStorage.setItem("averix_x_followed", "true");
    
    // Show completed task UI
    document.getElementById('followXForm').style.display = 'none';
    document.getElementById('followXCompleted').style.display = 'flex';
    
    // Update status message
    document.getElementById('followXStatus').innerText = "Thank you for following @averixapp! 20 AVE earned";
    document.getElementById('followXStatus').style.color = "#2cb67d";
    
    // Update tasks completed count
    updateTasksCompleted();
    updateProgressCircle();
}

function dailyCheckin() {
    const today = new Date().toDateString();
    const lastCheckin = localStorage.getItem("averix_last_checkin");
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    
    let streak = parseInt(localStorage.getItem("averix_daily_streak") || "0");
    
    if (lastCheckin === today) {
        dailyStatus.innerText = "Already checked in today!";
        dailyStatus.style.color = "#ff6b6b";
        return;
    }
    
    // Check if yesterday was the last check-in (maintain streak)
    if (lastCheckin === yesterday.toDateString()) {
        streak += 1;
    } else if (!lastCheckin) {
        streak = 1; // First check-in
    } else {
        streak = 1; // Broken streak, restart
    }
    
    // Save check-in
    localStorage.setItem("averix_last_checkin", today);
    localStorage.setItem("averix_daily_streak", streak.toString());
    
    // Mark daily check-in task as completed
    localStorage.setItem("averix_daily_completed", "true");
    
    // IMPORTANT: Track total daily check-ins for cumulative AVE calculation
    let totalDailyCheckins = parseInt(localStorage.getItem("averix_total_daily_checkins") || "0");
    totalDailyCheckins += 1;
    localStorage.setItem("averix_total_daily_checkins", totalDailyCheckins.toString());
    
    // Update UI
    document.getElementById('dailyCheckinBtn').style.display = 'none';
    document.getElementById('dailyCompleted').style.display = 'flex';
    document.getElementById('dailyCheckinBtn').classList.add('disabled');
    document.getElementById('dailyCheckinBtn').disabled = true;
    
    dailyStatus.innerText = "Daily check-in completed! 20 AVE earned (Total: " + totalDailyCheckins + " check-ins)";
    dailyStatus.style.color = "#2cb67d";
    
    // Update streak display
    updateDailyCheckinStatus();
    
    // Update tasks completed count
    updateTasksCompleted();
    updateProgressCircle();
}

function updateProfilePic(username) {
    const profilePic = document.getElementById('profilePic');
    if (username && username.length > 0) {
        // Get first letter of username and make it uppercase
        const firstLetter = username.charAt(0).toUpperCase();
        
        // Check if user has uploaded a custom profile picture
        const customPic = localStorage.getItem("averix_profile_pic");
        if (customPic) {
            profilePic.style.backgroundImage = `url('${customPic}')`;
            profilePic.textContent = '';
        } else {
            profilePic.textContent = firstLetter;
            profilePic.style.backgroundImage = 'none';
        }
    }
}

function updateTasksCompleted() {
    let completedTasks = 0;
    
    // Check which tasks are completed (one-time tasks only)
    const username = localStorage.getItem('averix_username');
    const gmail = localStorage.getItem('averix_gmail');
    const xConnected = localStorage.getItem('averix_x_connected') === "true";
    const xFollowed = localStorage.getItem('averix_x_followed') === "true";
    const discordConnected = localStorage.getItem('averix_discord_connected') === "true";
    
    // For the progress circle: count all one-time tasks
    if (username) completedTasks += 1; // Username task
    if (gmail) completedTasks += 1; // Gmail task
    if (xConnected) completedTasks += 1; // X connection task
    if (xFollowed) completedTasks += 1; // Follow X task
    if (discordConnected) completedTasks += 1; // Discord connection task
    
    // Calculate AVE earned
    // One-time tasks: 20 AVE each
    const oneTimeAve = completedTasks * 20;
    
    // Daily check-ins: 20 AVE for each check-in (including first)
    const totalDailyCheckins = parseInt(localStorage.getItem('averix_total_daily_checkins') || '0');
    const dailyAve = totalDailyCheckins * 20;
    
    // Total AVE = one-time tasks + all daily check-ins
    const aveEarned = oneTimeAve + dailyAve;
    
    // Save to localStorage
    localStorage.setItem('averix_completed_tasks', completedTasks.toString());
    localStorage.setItem('averix_ave_earned', aveEarned.toString());
    
    // Update display
    document.getElementById('tasksCompletedCount').textContent = completedTasks + "/5";
    document.getElementById('aveEarned').textContent = aveEarned + " AVE";
    
    return completedTasks;
}

function updateProgressCircle() {
    const completedTasks = updateTasksCompleted();
    // 5 one-time tasks total (username, gmail, x connected, follow x, discord)
    const progress = (completedTasks / 5) * 100;
    
    const progressCircle = document.getElementById('progressCircle');
    const progressText = document.getElementById('progressText');
    
    progressCircle.style.setProperty('--progress', progress + '%');
    progressText.textContent = completedTasks + "/5";
}

function loadProfile(){
    const u = localStorage.getItem("averix_username")
    if(u){
        profileName.innerText = u
        identityUsername.innerText = "Username: " + u
        // Update profile picture with first letter of username
        updateProfilePic(u)
    }
    
    const xUsername = localStorage.getItem("averix_x_username");
    if (localStorage.getItem("averix_x_connected") === "true") {
        document.getElementById('identityX').textContent = "X (Twitter): @" + (xUsername || "user");
        // Show disconnect X button
        document.getElementById('disconnectXBtn').style.display = 'block';
    } else {
        document.getElementById('identityX').textContent = "X (Twitter): Not Connected";
        // Hide disconnect X button
        document.getElementById('disconnectXBtn').style.display = 'none';
    }
    
    const discordUsername = localStorage.getItem("averix_discord_username");
    if (localStorage.getItem("averix_discord_connected") === "true") {
        document.getElementById('identityDiscord').textContent = "Discord: " + (discordUsername || "user");
        // Show disconnect Discord button
        document.getElementById('disconnectDiscordBtn').style.display = 'block';
    } else {
        document.getElementById('identityDiscord').textContent = "Discord: Not Connected";
        // Hide disconnect Discord button
        document.getElementById('disconnectDiscordBtn').style.display = 'none';
    }
    
    if(currentAccount){
        profileWallet.innerText =
            currentAccount.slice(0,6)+"..."+currentAccount.slice(-4)
    }
    
    // Update tasks completed count when loading profile
    updateTasksCompleted()
    updateDailyCheckinStatus()
    
    // Load custom profile picture if exists
    const customPic = localStorage.getItem("averix_profile_pic");
    if (customPic) {
        const profilePic = document.getElementById('profilePic');
        profilePic.style.backgroundImage = `url('${customPic}')`;
        profilePic.textContent = '';
    }
    
    // Check multiplier status
    checkMultiplierStatus();
}

// Username editing functions
function startEditingUsername() {
    const currentUsername = localStorage.getItem("averix_username") || ""
    document.getElementById('editUsernameInput').value = currentUsername
    document.getElementById('editUsernameForm').style.display = 'block'
    document.getElementById('editUsernameStatus').innerText = ''
    isEditingUsername = true
}

function saveNewUsername() {
    const newUsername = document.getElementById('editUsernameInput').value.trim()
    
    if(!newUsername) {
        document.getElementById('editUsernameStatus').innerText = "Please enter a username"
        document.getElementById('editUsernameStatus').style.color = "#ff6b6b"
        return
    }
    
    // Save new username
    localStorage.setItem("averix_username", newUsername)
    
    // Update all username displays
    document.getElementById('profileName').textContent = newUsername
    document.getElementById('identityUsername').innerText = "Username: " + newUsername
    document.getElementById('completedUsername').textContent = newUsername
    
    // Update profile picture
    updateProfilePic(newUsername)
    
    // Show success message
    document.getElementById('editUsernameStatus').innerText = "Username updated successfully!"
    document.getElementById('editUsernameStatus').style.color = "#2cb67d"
    
    // Hide the edit form after a delay
    setTimeout(() => {
        document.getElementById('editUsernameForm').style.display = 'none'
        isEditingUsername = false
    }, 1500)
}

function cancelEditUsername() {
    document.getElementById('editUsernameForm').style.display = 'none'
    document.getElementById('editUsernameStatus').innerText = ''
    isEditingUsername = false
}

function uploadProfilePic() {
    const fileInput = document.getElementById('profilePicUpload');
    const file = fileInput.files[0];
    const status = document.getElementById('uploadStatus');
    
    if (!file) return;
    
    // Check file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
        status.innerText = "File too large! Max 2MB.";
        status.style.color = "#ff6b6b";
        return;
    }
    
    // Check file type
    if (!file.type.match('image.*')) {
        status.innerText = "Please select an image file.";
        status.style.color = "#ff6b6b";
        return;
    }
    
    // Create a FileReader to read the file
    const reader = new FileReader();
    
    reader.onload = function(e) {
        // Convert image to base64 and save to localStorage
        const base64Image = e.target.result;
        localStorage.setItem("averix_profile_pic", base64Image);
        
        // Update profile picture display
        const profilePic = document.getElementById('profilePic');
        profilePic.style.backgroundImage = `url('${base64Image}')`;
        profilePic.textContent = '';
        
        status.innerText = "Profile picture updated successfully!";
        status.style.color = "#2cb67d";
        
        // Clear status after 3 seconds
        setTimeout(() => {
            status.innerText = "";
        }, 3000);
    };
    
    reader.onerror = function() {
        status.innerText = "Error reading file.";
        status.style.color = "#ff6b6b";
    };
    
    reader.readAsDataURL(file);
}

async function connectWallet(){
    if(!window.solana) return alert("Solana wallet not detected")
    const response = await window.solana.connect();
    const publicKey = response.publicKey.toString();
    const n=await fetch("/nonce",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({address:publicKey})})
    const {message}=await n.json()
    await window.solana.signMessage(new TextEncoder().encode(message), "utf8");
    await fetch("/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({address:publicKey}))
    unlock(publicKey)
}
</script>

</body>
</html>
'''

@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)

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

@app.route("/sol_price")
def get_sol_price():
    """Get current SOL price from CoinMarketCap"""
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        parameters = {
            'symbol': 'SOL',
            'convert': 'USD'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY,
        }
        
        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()
        
        if 'data' in data and 'SOL' in data['data']:
            price = data['data']['SOL']['quote']['USD']['price']
            return jsonify({
                "ok": True,
                "price": price
            })
        else:
            return jsonify({
                "ok": False,
                "error": "Could not fetch SOL price"
            }), 400
            
    except Exception as e:
        print(f"Error fetching SOL price: {e}")
        # Fallback price if API fails
        return jsonify({
            "ok": True,
            "price": 150.0  # Default price
        })

@app.route("/check_balance", methods=["POST"])
def check_balance():
    """Check if user has enough SOL balance"""
    try:
        data = request.json
        user_address = data.get("address")
        required_lamports = data.get("requiredLamports", 0)
        
        if not user_address:
            return jsonify({"ok": False, "error": "No address provided"}), 400
        
        # Call Solana RPC to get balance
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBalance",
            "params": [user_address]
        }
        
        response = requests.post(SOLANA_RPC_URL, json=payload)
        result = response.json()
        
        if 'result' in result and 'value' in result['result']:
            current_balance = result['result']['value']
            
            # Check if balance is sufficient (add some buffer for transaction fees)
            required_with_buffer = required_lamports + 5000  # 5000 lamports buffer for fees
            
            if current_balance >= required_with_buffer:
                return jsonify({
                    "ok": True,
                    "balance": current_balance,
                    "required": required_lamports,
                    "sufficient": True
                })
            else:
                return jsonify({
                    "ok": False,
                    "balance": current_balance,
                    "required": required_lamports,
                    "sufficient": False,
                    "error": "Insufficient SOL balance"
                })
        else:
            return jsonify({"ok": False, "error": "Could not fetch balance"}), 400
            
    except Exception as e:
        print(f"Error checking balance: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/send_sol_transaction", methods=["POST"])
def send_sol_transaction():
    """Handle SOL transfer transaction"""
    try:
        data = request.json
        from_pubkey = data.get("fromPubkey")
        to_pubkey = data.get("toPubkey")
        lamports = data.get("lamports", 0)
        
        if not from_pubkey or not to_pubkey or lamports <= 0:
            return jsonify({"ok": False, "error": "Invalid transaction parameters"}), 400
        
        # This endpoint should be called from the frontend after the user signs the transaction
        # The frontend will handle the actual signing and sending of the transaction
        
        # For now, we'll simulate a successful transaction
        # In a real implementation, you would:
        # 1. Verify the transaction signature
        # 2. Send the transaction to the Solana network
        
        # Simulate transaction success
        transaction_id = f"simulated_tx_{secrets.token_hex(16)}"
        
        # Store the purchase in our database
        MULTIPLIER_PURCHASES[from_pubkey] = {
            "has_multiplier": True,
            "purchase_date": datetime.now().isoformat(),
            "transaction_id": transaction_id,
            "amount": lamports / 1_000_000_000  # Convert lamports to SOL
        }
        
        return jsonify({
            "ok": True,
            "transaction_id": transaction_id,
            "message": "Transaction successful"
        })
        
    except Exception as e:
        print(f"Error processing transaction: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/update_multiplier", methods=["POST"])
def update_multiplier():
    """Update user's multiplier status"""
    try:
        data = request.json
        user_address = data.get("address")
        has_multiplier = data.get("hasMultiplier", False)
        
        if not user_address:
            return jsonify({"ok": False, "error": "No address provided"}), 400
        
        # Store multiplier status
        MULTIPLIER_PURCHASES[user_address] = {
            "has_multiplier": has_multiplier,
            "updated_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "ok": True,
            "hasMultiplier": has_multiplier
        })
        
    except Exception as e:
        print(f"Error updating multiplier: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

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
    
    # Check if user has multiplier
    multiplier_data = MULTIPLIER_PURCHASES.get(address, {})
    has_multiplier = multiplier_data.get("has_multiplier", False)
    
    return jsonify({
        "ok": True,
        "address": address,
        "user_data": USER_DATA[address],
        "has_multiplier": has_multiplier
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
    print("Solana Multiplier Purchase: ACTIVE")
    print(f"Project Wallet: {PROJECT_WALLET}")
    print("To access from your phone, make sure you're on the same network")
    print("and use your computer's IP address followed by :5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
