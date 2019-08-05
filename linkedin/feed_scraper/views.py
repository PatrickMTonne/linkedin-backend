from .models import Post

import boto3

s3 = boto3.client('s3')
rds = boto3.client('rds')


def lambda_handler(event, context):
    file_obj = event['Records'][0]
    filename = str(file_obj['s3']['object']['key'])
    file = s3.get_object(Bucket='sam-test-132', Key=filename)
    file_content = file['Body'].read().decode('utf-8')
    data = Post.scrape_feed(file_content)
    Post.create_posts(data, filename)
