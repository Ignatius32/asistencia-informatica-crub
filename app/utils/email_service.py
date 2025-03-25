import requests
import json
import os
from flask import current_app, url_for
import traceback

class EmailService:
    """
    Service to handle email communications for the help desk system.
    This service connects to Google Apps Script web app to send emails.
    """
    
    def __init__(self, deployment_url=None):
        """
        Initialize the email service with the GAS deployment URL.
        
        Args:
            deployment_url: URL to the deployed Google Apps Script web app
        """
        self.deployment_url = deployment_url or os.environ.get('GAS_DEPLOYMENT_URL')
        
    def _make_request(self, function_name, parameters):
        """
        Make an authenticated request to the Google Apps Script web app.
        
        Args:
            function_name: Name of the GAS function to call
            parameters: List of parameters for the function
            
        Returns:
            Dictionary with success status and message
        """
        if not self.deployment_url:
            error_msg = "GAS_DEPLOYMENT_URL no configurada. Revise su archivo .env."
            current_app.logger.error(error_msg)
            return {"success": False, "message": error_msg}
            
        try:
            current_app.logger.info(f"Intentando enviar correo usando la función: {function_name}")
            current_app.logger.debug(f"Parámetros del correo: {parameters}")
            
            payload = {
                "function": function_name,
                "parameters": parameters,
                "token": current_app.config.get('GOOGLE_DRIVE_SECURE_TOKEN')
            }
            
            if not payload["token"]:
                error_msg = "GOOGLE_DRIVE_SECURE_TOKEN no configurado. Revise su archivo .env."
                current_app.logger.error(error_msg)
                return {"success": False, "message": error_msg}
            
            current_app.logger.info(f"Making request to: {self.deployment_url}")
            response = requests.post(self.deployment_url, json=payload)
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get('success'):
                        current_app.logger.info(f"Correo enviado exitosamente usando {function_name}")
                        return {"success": True, "message": "Correo enviado exitosamente"}
                    else:
                        error_msg = f"Error de GAS: {response_data.get('error', 'Error desconocido')}"
                        current_app.logger.error(error_msg)
                        return {"success": False, "message": error_msg}
                except json.JSONDecodeError:
                    error_msg = f"Respuesta JSON inválida: {response.text}"
                    current_app.logger.error(error_msg)
                    return {"success": False, "message": error_msg}
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                current_app.logger.error(error_msg)
                return {"success": False, "message": error_msg}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Error de red al enviar correo: {str(e)}"
            current_app.logger.error(error_msg)
            current_app.logger.error(traceback.format_exc())
            return {"success": False, "message": error_msg}
        except Exception as e:
            error_msg = f"Error inesperado al enviar correo: {str(e)}"
            current_app.logger.error(error_msg)
            current_app.logger.error(traceback.format_exc())
            return {"success": False, "message": error_msg}
    
    def send_ticket_creation_notification(self, user_email, user_name, ticket_id, ticket_description, technician_name):
        """
        Send an email notification when a new ticket is created.
        
        Args:
            user_email: Email of the user who created the ticket
            user_name: Name of the user
            ticket_id: ID of the created ticket
            ticket_description: Description of the ticket
            technician_name: Name of the assigned technician
        
        Returns:
            Dictionary with success status and message
        """
        return self._make_request("sendTicketCreationNotification", [
            user_email,
            user_name,
            ticket_id,
            ticket_description,
            technician_name
        ])
    
    def send_ticket_status_update(self, user_email, user_name, ticket_id, ticket_description, status, technician_name, solution=None):
        """
        Send an email notification when a ticket status is updated.
        
        Args:
            user_email: Email of the user who owns the ticket
            user_name: Name of the user
            ticket_id: ID of the ticket
            ticket_description: Description of the ticket
            status: New status of the ticket
            technician_name: Name of the assigned technician
            solution: Solution description (only when ticket is closed)
        
        Returns:
            Dictionary with success status and message
        """
        return self._make_request("sendTicketStatusUpdateNotification", [
            user_email,
            user_name,
            ticket_id,
            ticket_description,
            status,
            technician_name,
            solution
        ])
    
    def send_technician_daily_summary(self, technician_email, technician_name, open_tickets, closed_today):
        """
        Send a daily summary email to technicians with their ticket stats.
        
        Args:
            technician_email: Email of the technician
            technician_name: Name of the technician
            open_tickets: Number of open tickets assigned to the technician
            closed_today: Number of tickets closed today by the technician
        
        Returns:
            Dictionary with success status and message
        """
        return self._make_request("sendTechnicianDailySummary", [
            technician_email,
            technician_name,
            open_tickets,
            closed_today
        ])
    
    def send_password_setup_email(self, user_email, user_name, token):
        """
        Send an email with a link to set up the user's password.
        
        Args:
            user_email: Email of the user
            user_name: Name of the user
            token: Password setup token
        
        Returns:
            Dictionary with success status and message
        """
        try:
            current_app.logger.info(f"Intentando enviar correo de configuración de contraseña a {user_email}")
            result = self._make_request("sendPasswordSetupEmail", [
                user_email,
                user_name,
                token
            ])
            if not result["success"]:
                current_app.logger.error(f"Error al enviar correo de configuración de contraseña: {result['message']}")
            return result
        except Exception as e:
            error_msg = f"Excepción al enviar correo de configuración de contraseña: {str(e)}"
            current_app.logger.error(error_msg)
            return {"success": False, "message": error_msg}