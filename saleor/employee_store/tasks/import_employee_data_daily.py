import csv
import re
import boto3
import datetime

from pprint import pprint
from random import randint
from time import sleep
from ...celeryconf import app
from .. import AuthTypes
from ..utils import get_channel_from_country_code
from ..email_handler import send_email_report
from ...account.models import User

from django.conf import settings

@app.task
def import_data(manual=False):
    pprint("*********************************************")
    pprint("********** vox_update_users_daily ***********")
    pprint("*********************************************")

    # Try to prevent the same job running multiple times.  The site is load banaced
    # so the job is running multiple times causing duplicate inventory updates. When
    # a job start and completes the status will be update but there is a race condition
    # when the status doesn't update quickly enough.
    if manual:
        delay_seconds = 1
    else:
        delay_seconds = randint(10,1800)

    pprint("Delaying Import by "+str(delay_seconds)+" seconds")
    sleep(delay_seconds)

    # Retrieve the list of existing buckets
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_DATA_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_DATA_SECRET_ACCESS_KEY
    )

    # Email Validation Reqex
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

    email_report_message = ""
    errors = ""
    updated_count = 0
    created_count = 0
    error_count = 0

    try:
        # Get yesterdays data formatted
        yesterday = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=1)
        import_file_date = yesterday.strftime("%m.%d.%Y")
        if manual:
            import_file_name = 'EE Import - Manual.csv'
        else:
            import_file_name = 'Employee Export - Daily Changes '+ import_file_date +'.csv'

        # Import File From S3
        s3_client = boto3.client('s3')
        s3_response_object = s3_client.get_object(Bucket=settings.AWS_DATA_BUCKET_NAME, Key=import_file_name)

        if "Metadata" in s3_response_object:
            if "importstatus" in s3_response_object['Metadata']:
                if s3_response_object['Metadata']['importstatus']:
                    if s3_response_object['Metadata']['importstatus'] == "SUCCESS":
                        email_report_message = "The daily user file has already been imported"
                        return False, email_report_message

        lines = s3_response_object['Body'].read().decode('utf-8').splitlines(True)
        reader = csv.reader(lines)
        next(reader, None)  # skip the headers
        for row in reader:
            email = row[4]
            name = row[1]
            points = row[5]
            order_allowance = row[6]
            change_type = row[7]
            country = row[8]
            default_channel = get_channel_from_country_code(country)
            auth_type = AuthTypes.OKTA

            # Validate the data
            if not re.match(regex,str(email)):
                pprint("********* Invalid Email: " + str(email))
                errors += "Invalid Email: "+str(email)+"\n"
                error_count+=1
                continue

            email = email.lower()

            # validate the change type
            if change_type != "New Hire" and change_type != "Termination" and change_type != "Data change" and change_type != "Points Change - Manual" and change_type != "Points Change - Manual Add":
                pprint("********* Invalid Change Type: " + str(email) + " : " + str(change_type))
                errors += "Invalid Change Type: "+str(email)+" : "+str(change_type)+"\n"
                error_count+=1
                continue

            if email is not None:
                user = User.objects.filter(email=email).first()
                if user is not None:
                    if change_type == "Termination":
                        user.is_active=False
                        user.save()
                        pprint("********* Deactivate User: "  + str(email) + " : " + str(name))
                        updated_count+=1
                    if change_type == "Data change":
                        # If the prevous points_reset_amount is less that the new points
                        # the user has changed to FT so add the extra points for this month
                        if int(points) > int(user.metadata["points_allowance"]):
                            user.metadata["points"]=str(int(points) - int(user.metadata["points_allowance"]) + int(user.metadata["points"]))
                        user.first_name=name
                        user.save()
                        updated_count+=1
                    if manual and change_type == "Points Change - Manual":
                        user.metadata["points"]=points
                        user.save()
                        updated_count+=1
                    if manual and change_type == "Points Change - Manual Add":
                        user.metadata["points"]=str(int(user.metadata['points']) + int(points))
                        user.save()
                        updated_count+=1
                else:
                    if change_type == "New Hire":
                        User.objects.create_user(
                            first_name=name,
                            email=email,
                            metadata={"points": points, "orders_remaining": order_allowance, "country": country.lower(), "default_channel": default_channel, "auth_type": auth_type},
                        )
                        created_count+=1
                    else:
                        error_count+=1

        now = datetime.datetime.now(tz=datetime.UTC)
        import_date = now.strftime("%m/%d/%Y %H:%M:%S")

        s3_client.copy_object(Key=import_file_name, Bucket=settings.AWS_DATA_BUCKET_NAME,
               CopySource={"Bucket": settings.AWS_DATA_BUCKET_NAME, "Key": import_file_name},
               Metadata={"ImportStatus": "SUCCESS", "ImportDate": import_date},
               MetadataDirective="REPLACE")

        email_report_message = "The daily user file has been imported successfully"

        return True, email_report_message
    except Exception as e:
        email_report_message = "An error occurred while importing the daily user file: "+str(e)
        return False, e
    finally:
        send_email_report("Daily User Import Report", email_report_message, errors, created_count, updated_count, error_count)
