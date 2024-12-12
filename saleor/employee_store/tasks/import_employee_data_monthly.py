import csv
import re
import boto3

from pprint import pprint
from ...celeryconf import app
from .. import AuthTypes
from ..utils import get_channel_from_country_code
from ..email_handler import send_email_report
from ...account.models import User

from django.conf import settings

@app.task
def import_data():
    pprint("*********************************************")
    pprint("********** vox_update_users_monthly *********")
    pprint("*********************************************")

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
        import_file_name = 'EE Export - Full File.csv'

        # Import File From S3
        s3_client = boto3.client('s3')
        s3_response_object = s3_client.get_object(Bucket=settings.AWS_DATA_BUCKET_NAME, Key=import_file_name)

        if "Metadata" in s3_response_object:
            if "importstatus" in s3_response_object['Metadata']:
                if s3_response_object['Metadata']['importstatus']:
                    if s3_response_object['Metadata']['importstatus'] == "SUCCESS":
                        email_report_message = "The monthly user file has already been imported"
                        return False, email_report_message

        lines = s3_response_object['Body'].read().decode('utf-8').splitlines(True)
        reader = csv.reader(lines)
        next(reader, None)  # skip the headers
        for row in reader:
            email = row[4]
            name = row[1]
            points = row[5]
            order_allowance = row[6]
            try:
                auth_type = getattr(AuthTypes, row[7])
            except IndexError:
                auth_type = AuthTypes.OKTA
            except AttributeError:
                auth_type = AuthTypes.OKTA
            country = row[8]

            default_channel = get_channel_from_country_code(country)

            # Validate the data
            if not re.match(regex,str(email)):
                errors += "Invalid Email: "+str(email)+"\n"
                error_count+=1
                continue

            if points is None or int(points) <= 0:
                errors += "Invalid Points: "+str(points)+" ("+str(email)+")\n"
                error_count+=1
                points = 0

            if order_allowance is None or int(order_allowance) <= 0:
                errors += "Invalid Order Allowance: "+str(order_allowance)+" ("+str(email)+")\n"
                error_count+=1
                order_allowance = 0

            if country is None:
                errors += "Invalid Country: "+str(country)+" ("+str(email)+")\n"
                error_count+=1
                points = 0

            email = email.lower()
            if email is not None:
                user = User.objects.filter(email=email).first()
                if user is not None:
                    user.first_name=name
                    user.metadata.update({"points": points, "points_allowance": points, "orders_remaining": order_allowance, "country": country.lower(), "default_channel": default_channel, "auth_type": auth_type})
                    user.save()
                    updated_count+=1
                else:
                    user = User.objects.create_user(
                        first_name=name,
                        email=email,
                        metadata={"points": points,  "points_allowance": points, "orders_remaining": order_allowance, "country": country.lower(), "default_channel": default_channel, "auth_type": auth_type},
                    )
                    created_count+=1

        s3_client.copy_object(Key=import_file_name, Bucket=settings.AWS_DATA_BUCKET_NAME,
            CopySource={"Bucket": settings.AWS_DATA_BUCKET_NAME, "Key": import_file_name},
            Metadata={"ImportStatus": "SUCCESS"},
            MetadataDirective="REPLACE")

        email_report_message = "The monthly user file has been imported successfully"

        return True, email_report_message
    except Exception as e:
        email_report_message = "An error occurred while importing the monthly user file: "+str(e)
        return False, e
    finally:
        send_email_report("Monthly User Import Report", email_report_message, errors, created_count, updated_count, error_count)

