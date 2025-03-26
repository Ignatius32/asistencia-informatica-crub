// Function to validate the security token
function validateToken(token) {
  const validToken = PropertiesService.getScriptProperties().getProperty('GOOGLE_DRIVE_SECURE_TOKEN');
  Logger.log("Validating token: " + token);
  Logger.log("Valid token from properties: " + validToken);
  return token === validToken;
}

// Function to handle GET requests - required for deployment
function doGet(e) {
  return ContentService.createTextOutput(JSON.stringify({
    status: "ok",
    message: "Email service is running"
  })).setMimeType(ContentService.MimeType.JSON);
}

// Function to handle POST requests
function doPost(e) {
  try {
    Logger.log("Received POST request: " + e.postData.contents);
    const data = JSON.parse(e.postData.contents);
    
    // Validate the security token
    if (!validateToken(data.token)) {
      Logger.log("Token validation failed");
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: "Invalid security token"
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Call the requested function with the provided parameters
    Logger.log("Calling function: " + data.function);
    const result = this[data.function].apply(this, data.parameters);
    Logger.log("Function result: " + JSON.stringify(result));
    
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      result: result
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    Logger.log("Error in doPost: " + error.toString());
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

// Function to send email with placeholder support
function sendEmail(to, subject, htmlBody, senderName, placeholders) {
  // Basic validation
  if (!to || !subject || !htmlBody) {
    throw new Error("Recipient, subject, and body are required.");
  }

  try {
    // Add common CSS styles to all emails
    const commonStyles = `
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          line-height: 1.6;
          color: #333;
          margin: 0;
          padding: 0;
        }
        .email-container {
          max-width: 600px;
          margin: 0 auto;
          padding: 20px;
          background: #ffffff;
        }
        .header {
          background: #2c3e50;
          color: #ffffff;
          padding: 20px;
          text-align: center;
          border-radius: 8px 8px 0 0;
          margin-bottom: 20px;
        }
        .header h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 600;
        }
        .content {
          padding: 20px;
          background: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 20px;
        }
        .details {
          background: #ffffff;
          padding: 15px;
          border-radius: 6px;
          border: 1px solid #e0e0e0;
          margin: 15px 0;
        }
        .details ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .details li {
          padding: 8px 0;
          border-bottom: 1px solid #eee;
        }
        .details li:last-child {
          border-bottom: none;
        }
        .button {
          display: inline-block;
          padding: 12px 24px;
          background-color: #3498db;
          color: #ffffff !important;
          text-decoration: none !important;
          border-radius: 4px;
          margin: 15px 0;
          font-weight: bold;
          text-align: center;
          border: none;
          box-shadow: 0 2px 5px rgba(0,0,0,0.1);
          transition: background-color 0.3s ease;
        }
        .button:hover {
          background-color: #2980b9;
        }
        .footer {
          text-align: center;
          padding: 20px;
          color: #666;
          font-size: 14px;
          border-top: 1px solid #eee;
        }
        .status-badge {
          display: inline-block;
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 14px;
          font-weight: 500;
        }
        .status-open {
          background-color: #fff3cd;
          color: #856404;
        }
        .status-in-progress {
          background-color: #cce5ff;
          color: #004085;
        }
        .status-closed {
          background-color: #d4edda;
          color: #155724;
        }
      </style>
    `;

    // Add the common styles to the HTML body
    htmlBody = commonStyles + htmlBody;
    
    // Process placeholders in subject and body if provided
    if (placeholders) {
      Object.keys(placeholders).forEach(function(key) {
        const placeholder = '<<' + key + '>>';
        subject = subject.replace(new RegExp(placeholder, 'g'), placeholders[key] || '');
        htmlBody = htmlBody.replace(new RegExp(placeholder, 'g'), placeholders[key] || '');
      });
    }
    
    // Configure email options
    let options = {
      htmlBody: htmlBody,
      name: senderName || 'Helpdesk System'
    };
    
    // Send the email
    GmailApp.sendEmail(to, subject, '', options);
    
    return {
      success: true,
      to: to,
      subject: subject
    };
  } catch (err) {
    Logger.log("Error sending email: " + err.message);
    return {
      success: false,
      error: err.message
    };
  }
}

// Function to send notification email for new tickets
function sendTicketCreationNotification(userEmail, userName, ticketId, ticketDescription, technicianName) {
  const subject = "Asistencia Informática CRUB-UNCo - Ticket #" + ticketId + " Creado";
  
  const htmlBody = `
    <div class="email-container">
      <div class="header">
        <h1>Ticket de Soporte Creado</h1>
      </div>
      
      <div class="content">
        <p>Hola <<userName>>,</p>
        <p>Su ticket de soporte ha sido creado exitosamente y asignado a un técnico.</p>
        
        <div class="details">
          <h3 style="margin-top: 0;">Detalles del Ticket:</h3>
          <ul>
            <li><strong>Número de Ticket:</strong> #<<ticketId>></li>
            <li><strong>Descripción:</strong> <<ticketDescription>></li>
            <li><strong>Técnico Asignado:</strong> <<technicianName>></li>
            <li><strong>Estado:</strong> <span class="status-badge status-open">Abierto</span></li>
          </ul>
        </div>
        
        <p>Le notificaremos cuando haya actualizaciones en su ticket.</p>
        <p>Gracias por usar nuestro sistema de Asistencia Informática CRUB-UNCo.</p>
      </div>
      
      <div class="footer">
        <p>Saludos cordiales,<br>Equipo de Asistencia Informática CRUB-UNCo</p>
      </div>
    </div>
  `;
  
  const placeholders = {
    userName: userName,
    ticketId: ticketId,
    ticketDescription: ticketDescription,
    technicianName: technicianName
  };
  
  return sendEmail(userEmail, subject, htmlBody, "Asistencia Informática CRUB-UNCo", placeholders);
}

// Function to send notification when ticket status changes
function sendTicketStatusUpdateNotification(userEmail, userName, ticketId, ticketDescription, status, technicianName, solution) {
  if (status === 'Closed') {
    // Send only solution email when ticket is closed
    const subject = "Solución para el Ticket #" + ticketId;
    const htmlBody = `
      <div class="email-container">
        <div class="header">
          <h1>Solución del Ticket</h1>
        </div>
        
        <div class="content">
          <p>Hola <<userName>>,</p>
          <p>Su ticket de soporte ha sido resuelto y cerrado.</p>
          
          <div class="details">
            <h3 style="margin-top: 0;">Detalles del Ticket:</h3>
            <ul>
              <li><strong>Número de Ticket:</strong> #<<ticketId>></li>
              <li><strong>Descripción:</strong> <<ticketDescription>></li>
              <li><strong>Técnico:</strong> <<technicianName>></li>
              <li><strong>Estado:</strong> <span class="status-badge status-closed">Cerrado</span></li>
              <li><strong>Solución:</strong> <<solution>></li>
            </ul>
          </div>
          
          <p>Si necesita más ayuda o si la solución no resolvió su problema, por favor cree un nuevo ticket.</p>
          <p>Gracias por usar nuestro sistema de Asistencia Informática CRUB-UNCo.</p>
        </div>
        
        <div class="footer">
          <p>Saludos cordiales,<br>Equipo de Asistencia Informática CRUB-UNCo</p>
        </div>
      </div>
    `;

    const placeholders = {
      userName: userName,
      ticketId: ticketId,
      ticketDescription: ticketDescription,
      technicianName: technicianName,
      solution: solution
    };
    
    return sendEmail(userEmail, subject, htmlBody, "Asistencia Informática CRUB-UNCo", placeholders);
  }
  return { success: true, message: "Not a closed ticket, no email needed" };
}

// Function to send daily summary to technicians
function sendTechnicianDailySummary(technicianEmail, technicianName, openTickets, closedToday) {
  const subject = "Resumen Diario de Tickets para " + technicianName;
  
  const htmlBody = `
    <div class="email-container">
      <div class="header">
        <h1>Resumen Diario de Tickets</h1>
      </div>
      
      <div class="content">
        <p>Hola <<technicianName>>,</p>
        <p>Aquí está su resumen diario de tickets:</p>
        
        <div class="details">
          <div style="display: flex; justify-content: space-around; text-align: center;">
            <div style="padding: 15px;">
              <div style="font-size: 36px; font-weight: 600; color: #3498db;"><<openTickets>></div>
              <div style="color: #666;">Tickets Abiertos</div>
            </div>
            <div style="padding: 15px;">
              <div style="font-size: 36px; font-weight: 600; color: #2ecc71;"><<closedToday>></div>
              <div style="color: #666;">Cerrados Hoy</div>
            </div>
          </div>
        </div>
        
        <p style="text-align: center;">
          <a href="https://huayca.crub.uncoma.edu.ar/asistencia-informatica/technician/dashboard" class="button">
            Ver Panel de Control
          </a>
        </p>
        
        <p>¡Gracias por su trabajo!</p>
      </div>
      
      <div class="footer">
        <p>Saludos cordiales,<br>Sistema de Asistencia Informática CRUB-UNCo</p>
      </div>
    </div>
  `;
  
  const placeholders = {
    technicianName: technicianName,
    openTickets: openTickets,
    closedToday: closedToday
  };
  
  return sendEmail(technicianEmail, subject, htmlBody, "Asistencia Informática CRUB-UNCo", placeholders);
}

// Function to send password setup email
function sendPasswordSetupEmail(userEmail, userName, token) {
  const subject = "Configure su Contraseña - Sistema de Asistencia Informática CRUB-UNCo";
  
  const htmlBody = `
    <div class="email-container">
      <div class="header">
        <h1>Bienvenido al Sistema de Asistencia Informática CRUB-UNCo</h1>
      </div>
      
      <div class="content">
        <p>Hola <<userName>>,</p>
        <p>Por favor haga clic en el siguiente botón para configurar su contraseña:</p>
        
        <p style="text-align: center;">
          <a href="https://huayca.crub.uncoma.edu.ar/asistencia-informatica/auth/set-password/<<token>>" class="button">
            Configurar Contraseña
          </a>
        </p>
        
        <div class="details">
          <p style="color: #666; font-size: 14px; margin: 0;">
            <strong>Nota:</strong> Este enlace expirará en 24 horas por razones de seguridad.
            Si no solicitó esto, por favor ignore este correo.
          </p>
        </div>
      </div>
      
      <div class="footer">
        <p>Saludos cordiales,<br>Equipo de Asistencia Informática CRUB-UNCo</p>
      </div>
    </div>
  `;
  
  const placeholders = {
    userName: userName,
    token: token
  };
  
  return sendEmail(userEmail, subject, htmlBody, "Asistencia Informática CRUB-UNCo", placeholders);
}