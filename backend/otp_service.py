"""
OTP (One-Time Password) service module.
Handles OTP generation, sending via Gmail SMTP, and verification.
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

# Email Configuration from environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'yashsih30@gmail.com')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', '')  # App-specific password from Gmail

# Log configuration on load
logger.info(f"OTP Service configured:")
logger.info(f"  SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
logger.info(f"  Sender Email: {SENDER_EMAIL}")
logger.info(f"  OTP Expiry: {OTP_EXPIRY_SECONDS} seconds")


def generate_otp() -> str:
    """
    Generate a random 6-digit OTP.
    
    Returns:
        6-digit OTP code as string
    """
    otp = ''.join([str(random.randint(0, 9)) for _ in range(OTP_LENGTH)])
    logger.info(f"[OTP] Generated OTP: {otp}")
    return otp


def send_otp_email(user_email: str, otp_code: str) -> bool:
    """
    Send OTP to user's email via Gmail SMTP.
    
    Args:
        user_email: Recipient email
        otp_code: OTP code to send
        
    Returns:
        True if sent successfully, False otherwise
    """
    try:
        logger.info(f"[OTP] Attempting to send OTP to {user_email}")
        
        # Check if credentials are set
        if not SENDER_PASSWORD:
            logger.error("[OTP] ✗ SENDER_PASSWORD not set in environment variables!")
            logger.warning("[OTP] To use Gmail SMTP:")
            logger.warning("[OTP]   1. Enable 2-Factor Authentication on your Gmail account")
            logger.warning("[OTP]   2. Generate an App Password at https://myaccount.google.com/apppasswords")
            logger.warning("[OTP]   3. Set SENDER_PASSWORD environment variable with the App Password")
            return False
        
        # Create email content
        subject = "Your Banking Authentication OTP"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #333; text-align: center;">🔐 Voice Banking Authentication</h2>
                    
                    <p style="font-size: 16px; color: #555; text-align: center; margin: 20px 0;">
                        Your OTP for login verification is:
                    </p>
                    
                    <div style="background-color: #007bff; color: white; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                        <h1 style="font-size: 48px; margin: 0; letter-spacing: 10px; font-weight: bold;">
                            {otp_code}
                        </h1>
                    </div>
                    
                    <p style="font-size: 14px; color: #666; text-align: center; margin: 20px 0;">
                        <strong>⏱️ This OTP expires in 5 minutes</strong>
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <p style="font-size: 13px; color: #999; text-align: center;">
                        If you did not request this OTP, please ignore this email and contact our support team immediately.
                    </p>
                    
                    <p style="font-size: 12px; color: #999; text-align: center; margin-top: 20px;">
                        This is an automated email. Do not reply to this message.
                    </p>
                </div>
            </body>
        </html>
        """
        
        plain_text = f"""
        Banking Authentication OTP
        ==========================
        
        Your OTP for login verification is: {otp_code}
        
        ⏱️ This OTP expires in 5 minutes
        
        If you did not request this OTP, please ignore this email.
        
        This is an automated email. Do not reply.
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = user_email
        
        # Attach both plain text and HTML versions
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        # Send email via Gmail SMTP
        try:
            logger.info(f"[OTP] Connecting to {SMTP_SERVER}:{SMTP_PORT}...")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                logger.info("[OTP] Starting TLS encryption...")
                server.starttls()
                
                logger.info("[OTP] Authenticating...")
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                
                logger.info(f"[OTP] Sending email to {user_email}...")
                server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
            
            logger.info(f"[OTP] ✓ OTP email sent successfully to {user_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[OTP] ✗ SMTP authentication failed: {e}")
            logger.error("[OTP] Check your SENDER_EMAIL and SENDER_PASSWORD in .env file")
            logger.error("[OTP] For Gmail, use an App Password, not your regular password")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"[OTP] ✗ SMTP error: {e}")
            return False
            
    except Exception as e:
        logger.error(f"[OTP] ✗ Failed to send OTP email: {e}")
        return False


def create_otp_for_user(user_id: int) -> dict:
    """
    Create and save OTP for user, then send via email.
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary with OTP info
    """
    try:
        logger.info(f"[OTP] Creating OTP for user {user_id}")
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Get user info
        user = db.get_user_by_id(user_id)
        if not user:
            logger.error(f"[OTP] User {user_id} not found")
            return {
                'success': False,
                'message': 'User not found'
            }
        
        user_email = user['email']
        logger.info(f"[OTP] User email: {user_email}")
        
        # Save OTP to database
        logger.info(f"[OTP] Saving OTP to database...")
        otp_id = db.save_otp(user_id, otp_code, OTP_EXPIRY_SECONDS)
        logger.info(f"[OTP] ✓ OTP saved with ID: {otp_id}")
        
        # Send OTP email
        logger.info(f"[OTP] Sending OTP email...")
        email_sent = send_otp_email(user_email, otp_code)
        
        if email_sent:
            logger.info(f"[OTP] ✓ OTP created and sent successfully")
            return {
                'success': True,
                'message': 'OTP sent to your email',
                'otp_id': otp_id,
                'expiry_seconds': OTP_EXPIRY_SECONDS,
                'email_sent': True
            }
        else:
            logger.warning(f"[OTP] ⚠ OTP created but email sending failed")
            logger.warning(f"[OTP] For testing, OTP is: {otp_code}")
            return {
                'success': False,
                'message': 'OTP created but email sending failed. Check SMTP configuration.',
                'otp_id': otp_id,
                'expiry_seconds': OTP_EXPIRY_SECONDS,
                'email_sent': False
            }
        
    except Exception as e:
        logger.error(f"[OTP] ✗ OTP creation failed: {e}")
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
        logger.info(f"[OTP] Verifying OTP for user {user_id}")
        
        # Check OTP
        is_valid = db.verify_otp(user_id, otp_code)
        
        if is_valid:
            logger.info(f"[OTP] ✓ OTP verified successfully for user {user_id}")
            return {
                'success': True,
                'message': 'OTP verified successfully',
                'user_id': user_id,
                'authenticated': True
            }
        else:
            logger.warning(f"[OTP] ✗ OTP verification failed for user {user_id}")
            return {
                'success': False,
                'message': 'Invalid or expired OTP',
                'user_id': user_id,
                'authenticated': False
            }
        
    except Exception as e:
        logger.error(f"[OTP] ✗ OTP verification error: {e}")
        return {
            'success': False,
            'message': f'OTP verification error: {str(e)}',
            'authenticated': False
        }

