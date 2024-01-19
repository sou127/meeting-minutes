from aws_cdk import aws_iam as iam, core

def setup_lambda_permissions(scope, lambda_function):
  lambda_function.add_to_role_policy(iam.PolicyStatement(
    actions=["lambda:*"],
    resources=["*"]
  ))

