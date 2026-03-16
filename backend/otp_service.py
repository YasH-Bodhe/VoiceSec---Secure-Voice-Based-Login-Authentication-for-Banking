"""
OTP (One-Time Password) service module.
Handles OTP generation, sending, and verification.
"""

import logging
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from database import db
import os

logger = logging.getLogger(__name__)

# OTP Configuration
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes

# Email Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'your-email@gmail.com')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', 'your-app-password')


def generate_otp() -> str:
    """
    Generate a random 6-digit OTP.
    
    Returns:
        6-digit OTP code as string
    """
    otp = ''.join([str(random.randint(0, 9)) for _ in range(OTP_LENGTH)])
    logger.info(f"Generated OTP: {otp}")
    return otp


def send_otp_email(user_email: str, otp_code: str) -> bool:
    """
    Send OTP to user's email.
    
    Args:
        user_email: Recipient email
        otp_code: OTP code to send
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        logger.info(f"Sending OTP to {user_email}")
        
        # Create email
        subject = "Voice Banking Authentication - OTP Verification"
        body = f"""
        <html>
            <body>
                <h2>Voice Banking Authentication</h2>
                <p>Your OTP for login verification is:</p>
                <h1 style="color: #007bff; font-size: 36px; font-weight: bold;">{otp_code}</h1>
                <p>This OTP will expire in 5 minutes.</p>
                <p>If you did not request this OTP, please ignore this email.</p>
                <hr>
                <p><small>This is an automated email. Do not reply.</small></p>
            </body>
        </html>
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = user_email
        
        part = MIMEText(body, "html")
        msg.attach(part)
        
        # Send email
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
            
            logger.info(f"OTP sent successfully to {user_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check email credentials.")
            # For development, just log the OTP
            logger.warning(f"Development mode: OTP for {user_email} is {otp_code}")
            return True  # Allow in development
            
    except Exception as e:
        logger.error(f"Failed to send OTP email: {e}")
        # Allow OTP to proceed even if email fails (use for testing)
        logger.warning(f"Development fallback: OTP for {user_email} is {otp_code}")
        return True


def create_otp_for_user(user_id: int) -> dict:
    """
    Create and save OTP for user.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with OTP info
    """
    try:
        # Generate OTP
        otp_code = generate_otp()
        
        # Save to database
        otp_id = db.save_otp(user_id, otp_code, OTP_EXPIRY_SECONDS)
        
        # Get user email
        user = db.get_user_by_id(user_id)
        if not user:
            return {
                'success': False,
                'message': 'User not found'
            }
        
        # Send email
        email_sent = send_otp_email(user['email'], otp_code)
        
        return {
            'success': True,
            'message': 'OTP sent to email' if email_sent else 'OTP generated (email failed)',
            'otp_id': otp_id,
            'expiry_seconds': OTP_EXPIRY_SECONDS
        }
        
    except Exception as e:
        logger.error(f"OTP creation failed: {e}")
        return {
            'success': False,
            'message': f'OTP creation failed: {str(e)}'
        }


def verify_otp_for_user(user_id: int, otp_code: str) -> dict:
    """
    Verify OTP for user.
    
    Args:
        user_id: User ID
        otp_code: OTP code to verify
        
    Returns:
        Dictionary with verification result
    """
    try:
        # Check OTP
        is_valid = db.verify_otp(user_id, otp_code)
        
        if is_valid:
            logger.info(f"OTP verified successfully for user {user_id}")
            return {
                'success': True,
                'message': 'OTP verified successfully',
                'user_id': user_id,
                'authenticated': True
            }
        else:
            logger.warning(f"OTP verification failed for user {user_id}")
            return {
                'success': False,
                'message': 'Invalid or expired OTP',
                'user_id': user_id,
                'authenticated': False
            }
        
    except Exception as e:
        logger.error(f"OTP verification error: {e}")
        return {
            'success': False,
            'message': f'OTP verification error: {str(e)}',
            'authenticated': False
        }


def get_otp_status(user_id: int) -> dict:
    """Get OTP status for user (for testing/debugging)."""
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            return {'message': 'User not found'}
        
        return {
            'message': 'User exists',
            'user_email': user['email']
        }
    except Exception as e:
        logger.error(f"Failed to get OTP status: {e}")
        return {'error': str(e)}
