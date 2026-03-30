# Admin Page

## Description
The Admin page provides user account management and system configuration options. It allows administrators to change passwords, manage settings, and access administrative functions.

## Purpose
- User account management
- Password change functionality
- System configuration
- User profile display
- Session management

## Features

### 1. User Profile Section
Displays current user information:
- User avatar (initials)
- Username
- Role (Administrator)
- Session status

### 2. Change Password Form
Secure password change functionality:

| Field | Description | Validation |
|-------|-------------|------------|
| **Old Password** | Current password | Required |
| **New Password** | New password | Min 6 chars |
| **Confirm Password** | Verify new password | Must match |

### 3. Account Settings
- Display name configuration
- Email preferences (if applicable)
- Notification settings

### 4. Session Information
- Login timestamp
- Session duration
- Last activity

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/check` | GET | Check authentication status |
| `/api/auth/change-password` | POST | Change password |
| `/api/auth/logout` | POST | End session |
| `/api/user/profile` | GET | Get user profile |
| `/api/user/settings` | GET/POST | User settings |

## Authentication System

### Login Flow
```python
@app.post("/api/auth/login")
async def login(request: LoginRequest):
    if verify_credentials(request.username, request.password):
        token = create_session(request.username)
        return {"status": "success", "token": token}
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

### Session Management
```python
sessions = {}  # In-memory session storage

def create_session(username):
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=8)
    }
    return token

def verify_session(token):
    if token in sessions:
        session = sessions[token]
        if session["expires_at"] > datetime.now():
            return session
    return None
```

### Password Change
```python
@app.post("/api/auth/change-password")
async def change_password(request: ChangePasswordRequest):
    # Verify old password
    if not verify_password(request.old_password, user.password_hash):
        raise HTTPException(400, "Incorrect old password")
    
    # Validate new password
    if request.new_password != request.confirm_password:
        raise HTTPException(400, "Passwords do not match")
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    return {"status": "success", "message": "Password changed"}
```

## Default Credentials

### Initial Setup
```python
DEFAULT_USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    }
}
```

> ⚠️ **Security Note**: Change default credentials immediately after installation!

## Technical Implementation

### Password Hashing
```python
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, stored_hash):
    return hash_password(password) == stored_hash
```

### Token-Based Authentication
```javascript
// Store token after login
localStorage.setItem('auth_token', response.token);

// Include token in API requests
fetch('/api/protected', {
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
    }
});
```

### JavaScript Functions
```javascript
handleChangePassword(event)   // Process password change
handleLogout()                // End session
checkAuthStatus()             // Verify authentication
updateUserProfile()           // Update display
```

## Form Validation

### Client-Side
```javascript
function validatePasswordChange() {
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword.length < 6) {
        showNotification('Password must be at least 6 characters', 'error');
        return false;
    }
    
    if (newPassword !== confirmPassword) {
        showNotification('Passwords do not match', 'error');
        return false;
    }
    
    return true;
}
```

### Server-Side
```python
class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
```

## Security Features

### Session Security
- Token expiration (8 hours)
- Secure token generation
- Session invalidation on logout

### Password Requirements
- Minimum 6 characters
- Server-side hashing (SHA-256)
- No plain-text storage

### Request Authentication
- Bearer token validation
- Protected route middleware
- Automatic redirect on expiration

## User Actions
- View profile information
- Change password
- Logout from session
- View session info

## Error Messages

| Error | Message | Action |
|-------|---------|--------|
| Wrong password | "Incorrect old password" | Re-enter password |
| Mismatch | "New passwords do not match" | Re-enter passwords |
| Session expired | "Session expired. Please login again" | Redirect to login |
| Unauthorized | "Not authenticated" | Redirect to login |

## Related Pages
- All pages (authentication required)
- Login page (session start)
