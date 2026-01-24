"""
Custom Email Backend to handle SSL certificate issues
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend


class CustomEmailBackend(EmailBackend):
    """
    Custom SMTP Email Backend that creates a less strict SSL context
    to handle certificate verification issues
    """
    
    def open(self):
        """
        Open the connection to the mail server with custom SSL context.
        """
        if self.connection:
            return False
        
        # Create a custom SSL context with less strict verification
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connection_params = {}
        if self.timeout is not None:
            connection_params['timeout'] = self.timeout
        
        if self.use_ssl:
            connection_params['context'] = ssl_context
            self.connection = smtplib.SMTP_SSL(
                self.host, 
                self.port, 
                **connection_params
            )
        else:
            self.connection = smtplib.SMTP(
                self.host, 
                self.port, 
                **connection_params
            )
            if self.use_tls:
                self.connection.starttls(context=ssl_context)
        
        if self.username and self.password:
            self.connection.login(self.username, self.password)
        
        return True


