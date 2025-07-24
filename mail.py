import os
import ssl
import socket
import imaplib
import tempfile

from email import policy
from email.parser import BytesParser

def email_connect(server: str, email_address: str, password: str):
    """Establish a secure IMAP connection and return the mailbox object."""
    mail = imaplib.IMAP4_SSL(server)
    mail.login(email_address, password)
    mail.select("INBOX")
    return mail

def email_get_unseen_msgs(mail) -> list:
    """Return list of unseen email IDs from the mailbox."""
    result, data = mail.search(None, 'UNSEEN')
    if result != 'OK' or not data[0]:
        return []
    return data[0].split()

def email_get_attachment(mail, email_id) -> str:
    """Download first attachment from the given email to a temp folder."""
    result, msg_data = mail.fetch(email_id, '(RFC822)')
    if result != 'OK':
        return None

    msg = BytesParser(policy=policy.default).parsebytes(msg_data[0][1])

    for part in msg.iter_attachments():
        filename = part.get_filename()
        if filename:
            temp_dir = tempfile.mkdtemp()
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))
            return filepath
    return None

def email_delete_msg(mail, email_id):
    """Mark email as deleted and remove it from the server."""
    mail.store(email_id, '+FLAGS', '\\Deleted')
    mail.expunge()


def email_check_msgs(email_server, email_address, email_password):
    """
    Checks if the mailbox is accessible and if any unseen messages exist.
    """
    try:
        mail = email_connect(email_server, email_address, email_password)
        email_ids = get_unseen_email_ids(mail)

        return mail, email_ids

    except imaplib.IMAP4.error:
        return None, "Invalid username or password"
    except socket.gaierror:
        return None, "Can't reach email server (DNS failure)"
    except socket.timeout:
        return None, "Email server connection timed out"
    except ssl.SSLError:
        return None, "SSL error – check port or encryption settings"
    except Exception as e:
        return None, f"Unexpected error: {e}"
