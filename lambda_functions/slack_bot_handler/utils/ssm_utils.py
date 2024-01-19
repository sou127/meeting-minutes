import boto3

def get_ssm_parameters(names):
    ssm = boto3.client("ssm")
    return [
        ssm.get_parameter(Name=f"/meeting_summarizer/{name}", WithDecryption=True)["Parameter"]["Value"]
        for name in names
    ]