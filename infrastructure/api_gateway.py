from aws_cdk import aws_apigateway as apigateway, core

def create_api_gateway(scope, app_name, lambda_handler):
  api = apigateway.RestApi(scope, f"{app_name}Api")
  api.root.add_method("POST", apigateway.LambdaIntegration(lambda_handler))
  return api