let currentAccount = null
let isEditingUsername = false

// Check and display completed tasks when page loads
document.addEventListener('DOMContentLoaded', function() {
    checkSavedWallet();
    checkCompletedTasks();
    updateDailyCheckinStatus();
    updateFollowXButton();
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
    if(tab==="refer") referPage.classList.remove("hidden")
    if(tab==="mult") {
        multPage.classList.remove("hidden")
        // No longer need to update AVE display since we removed it
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
    await fetch("/verify",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({address:publicKey})})
    unlock(publicKey)
}
