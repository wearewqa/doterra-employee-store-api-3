import datetime
from django.core.mail import send_mail

def send_email_report(subject, message, errors, created_count, updated_count, error_count):
    now = datetime.datetime.now(tz=datetime.UTC)
    import_date = now.strftime("%m/%d/%Y %H:%M:%S")

    email_message = subject
    email_message += "\r\n"
    email_message += "--------------------------------------------\r\n"
    email_message += "Import Date: "+import_date+"\r\n"
    email_message += message
    email_message += "\r\n"
    if created_count > 0:
        email_message += "Created Users: "+str(created_count)+"\r\n"
    if updated_count > 0:
        email_message += "Updated Users: "+str(updated_count)+"\r\n"
    if errors:
            email_message += "Monthly Import Errors: "+str(error_count)+"\r\n"
            email_message += "--------------------------------------------\r\n"
            email_message += errors
    email_message += "\r\n"

    send_mail(
        subject,
        email_message,
        'employeestore@doterra.com',
        ['matt.burns@wearewqa.com'],
        fail_silently=False,
    )
