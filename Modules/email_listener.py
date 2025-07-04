# import sqlite3
# from datetime import datetime
# import win32com.client
#
# #  Use your absolute DB path
# DB = r"C:\Users\GM612CD\PycharmProjects\UC_Agentic_AI_DLP\Modules\database.db"
#
#
# def store_email(employee, subject, body, destination):
#     conn = sqlite3.connect(DB)
#     c = conn.cursor()
#     c.execute(
#         """
#         INSERT INTO requests (employee, datetime, type, details, destination, status)
#         VALUES (?, ?, ?, ?, ?, ?)
#     """,
#         (
#             employee,
#             datetime.now().isoformat(),
#             "Email",
#             f"{subject}\n{body}",
#             destination,
#             "Pending",
#         ),
#     )
#     conn.commit()
#     conn.close()
#
#
# def check_mail():
#     outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
#     inbox = outlook.GetDefaultFolder(6)  # Inbox
#     messages = inbox.Items
#     messages = messages.Restrict("[Unread] = true")
#
#     for message in messages:
#         try:
#             # Skip if not a MailItem
#             if message.MessageClass != "IPM.Note":
#                 continue
#
#             subject = message.Subject
#
#             if subject and "TEST - DLP " in subject:
#                 # Defensive: Use Sender vs SenderEmailAddress
#                 try:
#                     from_ = message.SenderEmailAddress
#                 except Exception:
#                     from_ = message.Sender.Address
#
#                 to = message.To
#                 body = message.Body
#
#                 store_email(from_, subject, body, to)
#
#                 message.Unread = False
#
#         except Exception as e:
#             print(f"Error processing message: {e}")
#
#
# if __name__ == "__main__":
#     check_mail()

import sqlite3
from datetime import datetime
import os
import win32com.client
import hashlib

DB = r"C:\Users\GM612CD\PycharmProjects\UC_Agentic_AI_DLP\Modules\database.db"

ATTACHMENTS_DIR = r"C:\Users\GM612CD\PycharmProjects\UC_Agentic_AI_DLP\Attachments"
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)


def store_email(employee, subject, body, destination, attachment_info=None):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO requests (employee, datetime, type, details, destination, status, attachment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """,
        (
            employee,
            datetime.now().isoformat(),
            "Email",
            f"{subject}\n{body}",
            destination,
            "Pending",
            attachment_info  # <-- reuse the existing column
        ),
    )
    conn.commit()
    conn.close()


def hash_file(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def check_mail():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)
    messages = inbox.Items
    messages = messages.Restrict("[Unread] = true")

    for message in messages:
        try:
            if message.MessageClass != "IPM.Note":
                continue

            subject = message.Subject

            if subject and "TEST - DLP" in subject:
                try:
                    from_ = message.SenderEmailAddress
                except Exception:
                    from_ = message.Sender.Address

                to = message.To
                body = message.Body

                attachment_info = None

                if message.Attachments.Count > 0:
                    for i in range(1, message.Attachments.Count + 1):
                        attachment = message.Attachments.Item(i)
                        file_name = attachment.FileName

                        save_path = os.path.join(ATTACHMENTS_DIR, file_name)
                        attachment.SaveAsFile(save_path)

                        file_hash = hash_file(save_path)

                        # Combine path + hash for traceability
                        attachment_info = f"{save_path}::{file_hash}"

                        print(f"Attachment saved: {save_path}")
                        print(f"Attachment hash: {file_hash}")

                store_email(from_, subject, body, to, attachment_info)

                message.Unread = False

        except Exception as e:
            print(f"Error processing message: {e}")


if __name__ == "__main__":
    check_mail()
