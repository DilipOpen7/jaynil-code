import schedule
import time
import boto3
import datetime

def job():

	session1 = boto3.Session(
		aws_access_key_id='AKIAYM2WHP5AXF2F2R4Z',
		aws_secret_access_key='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',
		region_name='us-east-1'
	)
	s3 = session1.resource('s3')
	bucket_name = 'survey-logs-oeti'
	file_name = './logs'

	d = datetime.datetime.today()
	object_name = 'logs'+str(d)

	try:
		s3.meta.client.upload_file(file_name, bucket_name, object_name)
	except ClientError as e:
		logging.error(e)

schedule.every().day.at("02:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)

