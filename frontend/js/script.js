/**
 * Voice Banking Authentication System - Frontend JavaScript
 * Shared utilities and helper functions
 */

// API Base URL
const API_BASE_URL = 'http://localhost:8000';

/**
 * Make API request
 */
async function apiRequest(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API Error');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Check token validity
 */
function getStoredToken() {
    return localStorage.getItem('auth_token');
}

function saveToken(token) {
    localStorage.setItem('auth_token', token);
}

function clearToken() {
    localStorage.removeItem('auth_token');
}

/**
 * User identification
 */
function getCurrentUserId() {
    return localStorage.getItem('user_id');
}

function saveUserId(userId) {
    localStorage.setItem('user_id', userId);
}

function clearUserId() {
    localStorage.removeItem('user_id');
}

/**
 * Audio Recording Helper
 */
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.startTime = null;
        this.timerInterval = null;
    }

    async start() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };

            this.mediaRecorder.start();
            this.startTime = Date.now();

            return true;
        } catch (error) {
            console.error('Microphone error:', error);
            alert('Unable to access microphone: ' + error.message);
            return false;
        }
    }

    stop() {
        return new Promise((resolve) => {
            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                resolve(audioBlob);
            };

            this.mediaRecorder.stop();

            // Stop all tracks
            this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        });
    }

    getDuration() {
        if (!this.startTime) return 0;
        return Math.floor((Date.now() - this.startTime) / 1000);
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
}

/**
 * Utility Functions
 */

function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background-color: ${getTypeColor(type)};
        color: white;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, duration);
}

function getTypeColor(type) {
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#17a2b8'
    };
    return colors[type] || colors.info;
}

/**
 * Validation Functions
 */

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

function validateOTP(otp) {
    return /^\d{6}$/.test(otp);
}

/**
 * Local Storage Helpers
 */

const Storage = {
    setUser: (user) => localStorage.setItem('user', JSON.stringify(user)),
    getUser: () => {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },
    clearUser: () => localStorage.removeItem('user'),
    
    setToken: (token) => localStorage.setItem('token', token),
    getToken: () => localStorage.getItem('token'),
    clearToken: () => localStorage.removeItem('token'),
    
    clear: () => localStorage.clear()
};

/**
 * Initialize on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    // Check if user is already authenticated
    const token = Storage.getToken();
    if (token && window.location.pathname !== '/static/dashboard.html') {
        // Could redirect to dashboard if needed
    }
});

/**
 * Logout function
 */
function performLogout() {
    Storage.clear();
    window.location.href = '/static/index.html';
}

/**
 * Password Login Function
 */
async function passwordLogin() {
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const messageDiv = document.getElementById('password-message');
    
    // Validation
    if (!email || !password) {
        messageDiv.textContent = '❌ Please fill in all fields';
        messageDiv.className = 'message error';
        messageDiv.style.display = 'block';
        return;
    }
    
    if (!validateEmail(email)) {
        messageDiv.textContent = '❌ Invalid email format';
        messageDiv.className = 'message error';
        messageDiv.style.display = 'block';
        return;
    }
    
    if (!validatePassword(password)) {
        messageDiv.textContent = '❌ Password must be at least 6 characters';
        messageDiv.className = 'message error';
        messageDiv.style.display = 'block';
        return;
    }
    
    try {
        messageDiv.textContent = '⏳ Logging in...';
        messageDiv.className = 'message info';
        messageDiv.style.display = 'block';
        
        // Use FormData for form submission (not JSON)
        const formData = new FormData();
        formData.append('email', email);
        formData.append('password', password);
        
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            messageDiv.textContent = '❌ ' + (data.detail || data.message || 'Login failed');
            messageDiv.className = 'message error';
            messageDiv.style.display = 'block';
            return;
        }
        
        // Check if voice verification required
        if (data.next_step === 'voice_verification' || data.success) {
            messageDiv.textContent = '✅ Password verified! Proceeding to voice verification...';
            messageDiv.className = 'message success';
            messageDiv.style.display = 'block';
            
            // Save user info to localStorage AND update global variables
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_email', data.email);
            
            // Update global variables (from login.html)
            if (typeof currentUserId !== 'undefined') {
                currentUserId = data.user_id;
                currentUserEmail = data.email;
                console.log(`✓ Updated currentUserId: ${currentUserId}, currentUserEmail: ${currentUserEmail}`);
            }
            
            // Hide password login, show voice verification
            setTimeout(() => {
                document.getElementById('password-login').style.display = 'none';
                document.getElementById('voice-verify').style.display = 'block';
            }, 1500);
        } else {
            messageDiv.textContent = '✅ Login successful!';
            messageDiv.className = 'message success';
            messageDiv.style.display = 'block';
            
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('user_email', data.email);
            
            if (typeof currentUserId !== 'undefined') {
                currentUserId = data.user_id;
                currentUserEmail = data.email;
            }
        }
    } catch (error) {
        console.error('Login error:', error);
        messageDiv.textContent = '❌ Error: ' + error.message;
        messageDiv.className = 'message error';
        messageDiv.style.display = 'block';
    }
}

/**
 * Debug function for console testing
 */
window.DEBUG = {
    getUser: () => Storage.getUser(),
    getToken: () => Storage.getToken(),
    clearAll: () => Storage.clear(),
    apiTest: async (endpoint) => {
        try {
            const result = await apiRequest(endpoint);
            console.log('API Result:', result);
            return result;
        } catch (error) {
            console.error('API Error:', error);
        }
    }
};

console.log('Voice Banking Auth System Loaded');
console.log('Type DEBUG to access debug functions');
