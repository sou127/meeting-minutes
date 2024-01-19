from aws_cdk import aws_ssm as ssm, core
from config import SSM_PARAMETER_NAMES

def setup_ssm_parameters(scope, app_name, lambda_identifiers, lambda_functions):
  for param_name in SSM_PARAMETER_NAMES:
    for lambda_identifier, lambda_function in zip(lambda_identifiers, lambda_functions):
      construct_name = f"{app_name}-{param_name.replace('/', '')}-for-{lambda_identifier}"
      ssm_param = ssm.StringListParameter.from_string_list_parameter_name(
        scope, construct_name, param_name
      )
      ssm_param.grant_read(lambda_function)