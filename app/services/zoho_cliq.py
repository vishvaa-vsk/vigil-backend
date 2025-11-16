import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings


class ZohoChanClient:
    """
    Client for sending messages to Zoho Cliq channels via webhooks
    Sends messages as 'Vigil' bot, not as the user
    """
    
    def __init__(self):
        self.webhook_url = settings.zoho_cliq_webhook_url
        self.token = settings.zoho_cliq_token
        self.timeout = 10
        # Bot identity
        self.bot_name = "Vigil"
    
    async def send_message(
        self,
        text: str,
        card: Optional[Dict[str, Any]] = None,
        mentions: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send a message to Zoho Cliq channel as Vigil bot
        
        Args:
            text: Message text
            card: Optional card with title and color (minimal format)
            mentions: Optional list of user mentions
        
        Returns:
            Response from Zoho Cliq API
        """
        try:
            payload = {
                "text": text,
                "bot": {
                    "name": self.bot_name
                }
            }
            
            # Add card if provided (Zoho accepts only title + color)
            if card:
                payload["card"] = card
            
            # Add mentions if provided
            if mentions:
                payload["mentions"] = mentions
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                    }
                )
                
                # 200, 201, 204 are all successful responses
                if response.status_code in [200, 201, 204]:
                    print(f"✅ Message sent from Vigil bot (Status: {response.status_code})")
                    return {"status": "success", "code": response.status_code}
                else:
                    print(f"❌ Failed to send message: {response.status_code}")
                    print(f"Error: {response.text}")
                    return {
                        "status": "failed",
                        "code": response.status_code,
                        "error": response.text
                    }
        
        except httpx.TimeoutException:
            print("❌ Zoho Cliq request timeout")
            return {"status": "failed", "error": "Request timeout"}
        except Exception as e:
            print(f"❌ Error sending to Zoho Cliq: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def create_card(
        self,
        title: str,
        severity: str = "info"
    ) -> Dict[str, Any]:
        """
        Create a minimal card for Zoho Cliq (title + color only)
        
        Args:
            title: Card title
            severity: Alert severity (info, warning, error, critical)
        
        Returns:
            Zoho card JSON structure
        """
        
        # Color mapping based on severity
        severity_colors = {
            "info": "#4A90E2",      # Blue
            "warning": "#F5A623",   # Orange
            "error": "#D0021B",     # Red
            "critical": "#8B0000"   # Dark Red
        }
        
        color = severity_colors.get(severity, "#4A90E2")
        
        # Zoho only accepts title + color in cards
        return {
            "title": title,
            "color": color
        }
    
    async def send_alert(
        self,
        title: str,
        description: str,
        severity: str = "info",
        metadata: Optional[Dict[str, str]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        text_fallback: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a formatted alert to Zoho Cliq with card + rich text
        
        Args:
            title: Alert title
            description: Alert description
            severity: Alert severity level (info, warning, error, critical)
            metadata: Additional metadata to display as key-value pairs
            actions: Action buttons with label and url
            text_fallback: Custom fallback plain text
        
        Returns:
            Send result
        """
        
        # Severity emoji mapping
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = severity_emoji.get(severity, "ℹ️")
        
        # Build clean text message (no markdown formatting)
        text = f"{emoji} {title}\n\n{description}"
        
        # Add metadata as formatted bullet points
        if metadata:
            text += "\n\nDetails:\n"
            for key, value in metadata.items():
                text += f"• {key}: {value}\n"
        
        # Add action links
        if actions:
            text += "\n\nQuick Links:\n"
            for action in actions:
                text += f"• {action.get('label', 'Link')}: {action.get('url', '#')}\n"
        
        # Create minimal card (title + color only)
        card = self.create_card(title=title, severity=severity)
        
        # Send message with card as Vigil bot
        return await self.send_message(text=text, card=card)


# Singleton instance
zoho_client = ZohoChanClient()