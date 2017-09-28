
import boto3
from botocore.client import Config
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):

    # SNS Definitions
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:975855450853:deployPortfolioTopic')

    try:
        # S3 resource, bucket Definitions and variables
        s3 = boto3.resource('s3')
        ## Required if encryption support is not added by boto3
        ## s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        portfolio_bucket = s3.Bucket('portfolio.cnimbus.biz')
        build_bucket = s3.Bucket('portfoliobuild.cnimbus.biz')

        # Python StringIO function and file definition
        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj('portfoliobuild.zip', portfolio_zip)

        #Parsing the zip file in the target
        with zipfile.ZipFile(portfolio_zip) as myzip:
          for nm in myzip.namelist():
            obj = myzip.open(nm)
            #portfolio_bucket.upload_fileobj(obj,nm)
            portfolio_bucket.upload_fileobj(obj,nm,
                ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
            portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        # Output for log
        print "Portfolio updated!"

        # SNS Publish action to notify us in email
        topic.publish(Subject="Portfolio deployed",Message="Portfolio deployment was successfull!")

    except:
        # SNS Publish action to warn us in email
        topic.publish(Subject="Portfolio deploy failed",Message="Portfolio deployment was NOT successfull!")

    return 'Portfolio Lambda action completed'
    
