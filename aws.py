import boto3

# Укажите учетные данные и конфигурацию явно
aws_access_key_id = 'AKIAWNOMKDH4LH776PI2'
aws_secret_access_key = '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'
aws_region = 'eu-north-1'

sns = boto3.client(
    service_name = 'sns',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)


sqs =  boto3.client(
    service_name = 'sqs',
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name=aws_region
)