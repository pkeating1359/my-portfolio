
import boto3
from botocore.client import Config
import StringIO
import zipfile
import mimetypes

def lambda_handler(event, context):

    # SNS Definitions
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:975855450853:deployPortfolioTopic')

    # Default locations if we are not executing from codepipeline
    location = {
        "bucketName": 'portfoliobuild.cnimbus.biz',
        "objectKey": 'portfoliobuild.zip'
    }

    try:
        #Codepipeline job event definition
        job = event.get("CodePipeline.job")

        # if we are running from codepipline parse the job artifacts
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3location"]

        print "Building portfolio from " + str(location)

        # S3 resource, bucket Definitions and variables
        s3 = boto3.resource('s3')
        ## Required if encryption support is not added by boto3
        ## s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))

        portfolio_bucket = s3.Bucket('portfolio.cnimbus.biz')

        build_bucket = s3.Bucket(location["bucketName"])
        #build_bucket = s3.Bucket('portfoliobuild.cnimbus.biz')

        # Python StringIO function and file definition
        portfolio_zip = StringIO.StringIO()

        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)
        #build_bucket.download_fileobj('portfoliobuild.zip', portfolio_zip)

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

        # Let codepipeline know the job status
        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job["id"])

    except:
        # SNS Publish action to warn us in email
        topic.publish(Subject="Portfolio deploy failed",Message="Portfolio deployment was NOT successfull!")

    return 'Portfolio Lambda action completed'
    
