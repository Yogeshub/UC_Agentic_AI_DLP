import sqlite3
from datetime import datetime
import win32com.client

#  Use your absolute DB path
DB = r"C:\Users\GM612CD\PycharmProjects\UC_Agentic_AI_DLP\database.db"
def store_email(employee, subject, body, destination):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        INSERT INTO requests (employee, datetime, type, details, destination, status) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (employee, datetime.now().isoformat(), "Email", f"{subject}\n{body}", destination, "Pending"))
    conn.commit()
    conn.close()

def check_mail():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)  # Inbox
    messages = inbox.Items
    messages = messages.Restrict("[Unread] = true")

    for message in messages:
        try:
            # Skip if not a MailItem
            if message.MessageClass != "IPM.Note":
                continue

            subject = message.Subject

            if subject and "TEST - DLP" in subject:
                # Defensive: Use Sender vs SenderEmailAddress
                try:
                    from_ = message.SenderEmailAddress
                except Exception:
                    from_ = message.Sender.Address

                to = message.To
                body = message.Body

                store_email(from_, subject, body, to)

                message.Unread = False

        except Exception as e:
            print(f"Error processing message: {e}")

if __name__ == "__main__":
    check_mail()