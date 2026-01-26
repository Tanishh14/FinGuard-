"""
Alerting service for sending notifications about high-risk transactions
"""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from loguru import logger

from app.core.config import settings


class AlertingService:
    """Service for sending fraud alerts via multiple channels"""
    
    def __init__(self):
        self.telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = settings.TELEGRAM_CHAT_ID
        self.smtp_config = {
            "server": settings.SMTP_SERVER,
            "port": settings.SMTP_PORT,
            "username": settings.SMTP_USERNAME,
            "password": settings.SMTP_PASSWORD,
            "from_email": settings.ALERT_EMAIL_FROM
        }
    
    async def send_fraud_alert(self, transaction_id: str, risk_score: float, risk_level: str, 
                              transaction_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send fraud alert through configured channels
        
        Returns:
            bool: True if at least one channel succeeded
        """
        channels = []
        
        # Add channels based on configuration
        if self.telegram_bot_token and self.telegram_chat_id:
            channels.append(self._send_telegram_alert)
        
        if self.smtp_config["username"] and self.smtp_config["password"]:
            channels.append(self._send_email_alert)
        
        # Send alerts through all channels
        results = []
        for channel in channels:
            try:
                success = await channel(transaction_id, risk_score, risk_level, transaction_data)
                results.append(success)
            except Exception as e:
                logger.error(f"Alert channel failed: {e}")
                results.append(False)
        
        # Return True if at least one channel succeeded
        return any(results)
    
    async def send_batch_alerts(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send alerts for multiple transactions"""
        logger.info(f"Sending batch alerts for {len(alerts)} transactions")
        
        summary = {
            "total_alerts": len(alerts),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for alert in alerts:
            try:
                success = await self.send_fraud_alert(
                    transaction_id=alert.get("transaction_id"),
                    risk_score=alert.get("risk_score", 0),
                    risk_level=alert.get("risk_level", "medium"),
                    transaction_data=alert.get("transaction_data")
                )
                
                if success:
                    summary["successful"] += 1
                    summary["details"].append({
                        "transaction_id": alert.get("transaction_id"),
                        "status": "sent"
                    })
                else:
                    summary["failed"] += 1
                    summary["details"].append({
                        "transaction_id": alert.get("transaction_id"),
                        "status": "failed"
                    })
                    
            except Exception as e:
                logger.error(f"Failed to send alert for {alert.get('transaction_id')}: {e}")
                summary["failed"] += 1
                summary["details"].append({
                    "transaction_id": alert.get("transaction_id"),
                    "status": "error",
                    "error": str(e)
                })
        
        return summary
    
    async def _send_telegram_alert(self, transaction_id: str, risk_score: float, 
                                  risk_level: str, transaction_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send alert via Telegram bot"""
        try:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                return False
            
            # Create alert message
            message = self._create_alert_message(transaction_id, risk_score, risk_level, transaction_data)
            
            # Send via Telegram API
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Telegram alert failed: {e}")
            return False
    
    async def _send_email_alert(self, transaction_id: str, risk_score: float, 
                               risk_level: str, transaction_data: Optional[Dict[str, Any]] = None) -> bool:
        """Send alert via email"""
        try:
            if not self.smtp_config["username"] or not self.smtp_config["password"]:
                return False
            
            # Create email message
            subject = f"🚨 FinGuard Alert: {risk_level.upper()} Risk Transaction Detected"
            body = self._create_email_body(transaction_id, risk_score, risk_level, transaction_data)
            
            # Setup email
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config["from_email"]
            msg["To"] = "security@finguard-ai.com"  # In production, this would come from settings
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_config["server"], self.smtp_config["port"]) as server:
                server.starttls()
                server.login(self.smtp_config["username"], self.smtp_config["password"])
                server.send_message(msg)
            
            logger.info(f"Email alert sent for transaction {transaction_id}")
            return True
            
        except Exception as e:
            logger.error(f"Email alert failed: {e}")
            return False
    
    def _create_alert_message(self, transaction_id: str, risk_score: float, 
                             risk_level: str, transaction_data: Optional[Dict[str, Any]] = None) -> str:
        """Create formatted alert message"""
        emoji = "🔴" if risk_level in ["high", "critical"] else "🟡" if risk_level == "medium" else "🟢"
        
        message = f"""
{emoji} <b>FinGuard Fraud Alert</b>
━━━━━━━━━━━━━━━━━━━━
<b>Transaction ID:</b> {transaction_id}
<b>Risk Level:</b> {risk_level.upper()}
<b>Risk Score:</b> {risk_score:.1f}
<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        if transaction_data:
            message += f"""
<b>Amount:</b> ${transaction_data.get('amount', 0):.2f}
<b>Merchant:</b> {transaction_data.get('merchant_id', 'Unknown')}
<b>Location:</b> {transaction_data.get('location_city', 'Unknown')}, {transaction_data.get('location_country', 'Unknown')}
"""
        
        message += "\n⚠️ <i>Review immediately in dashboard</i>"
        return message.strip()
    
    def _create_email_body(self, transaction_id: str, risk_score: float, 
                          risk_level: str, transaction_data: Optional[Dict[str, Any]] = None) -> str:
        """Create HTML email body"""
        color = "#dc3545" if risk_level in ["high", "critical"] else "#ffc107" if risk_level == "medium" else "#28a745"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .alert {{ border-left: 4px solid {color}; padding: 15px; background-color: #f8f9fa; }}
        .header {{ color: {color}; font-size: 18px; font-weight: bold; }}
        .details {{ margin-top: 15px; }}
        .detail-row {{ margin: 5px 0; }}
        .label {{ font-weight: bold; display: inline-block; width: 120px; }}
        .action {{ margin-top: 20px; padding: 10px; background-color: #e9ecef; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="alert">
        <div class="header">🚨 Fraud Alert: {risk_level.upper()} Risk Detected</div>
        <div class="details">
            <div class="detail-row"><span class="label">Transaction ID:</span> {transaction_id}</div>
            <div class="detail-row"><span class="label">Risk Level:</span> <span style="color: {color};">{risk_level.upper()}</span></div>
            <div class="detail-row"><span class="label">Risk Score:</span> {risk_score:.1f}/100</div>
            <div class="detail-row"><span class="label">Time:</span> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        """
        
        if transaction_data:
            html += f"""
            <div class="detail-row"><span class="label">Amount:</span> ${transaction_data.get('amount', 0):.2f}</div>
            <div class="detail-row"><span class="label">Merchant:</span> {transaction_data.get('merchant_id', 'Unknown')}</div>
            <div class="detail-row"><span class="label">Location:</span> {transaction_data.get('location_city', 'Unknown')}, {transaction_data.get('location_country', 'Unknown')}</div>
            """
        
        html += f"""
        </div>
        <div class="action">
            <strong>Recommended Action:</strong> 
            {'Block transaction and investigate immediately' if risk_level in ['high', 'critical'] else 'Review transaction and consider additional verification'}
        </div>
        <p style="margin-top: 20px;">
            <a href="https://finguard-ai.com/dashboard/alerts" style="background-color: {color}; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px;">
                Review in Dashboard
            </a>
        </p>
    </div>
</body>
</html>
        """
        
        return html
    
    async def test_alert_channels(self) -> Dict[str, bool]:
        """Test all configured alert channels"""
        test_transaction = {
            "transaction_id": "test_alert_123",
            "risk_score": 85.5,
            "risk_level": "high",
            "amount": 1000.00,
            "merchant_id": "test_merchant",
            "location_city": "Test City",
            "location_country": "TC"
        }
        
        results = {}
        
        # Test Telegram
        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                success = await self._send_telegram_alert(
                    transaction_id=test_transaction["transaction_id"],
                    risk_score=test_transaction["risk_score"],
                    risk_level=test_transaction["risk_level"],
                    transaction_data=test_transaction
                )
                results["telegram"] = success
            except Exception as e:
                logger.error(f"Telegram test failed: {e}")
                results["telegram"] = False
        
        # Test Email
        if self.smtp_config["username"] and self.smtp_config["password"]:
            try:
                success = await self._send_email_alert(
                    transaction_id=test_transaction["transaction_id"],
                    risk_score=test_transaction["risk_score"],
                    risk_level=test_transaction["risk_level"],
                    transaction_data=test_transaction
                )
                results["email"] = success
            except Exception as e:
                logger.error(f"Email test failed: {e}")
                results["email"] = False
        
        return results