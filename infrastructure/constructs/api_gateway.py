from aws_cdk import (
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_cognito as cognito,
)
from constructs import Construct


class ApiGatewayConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, lambda_functions=None) -> None:
        super().__init__(scope, construct_id)
        
        # Create Cognito User Pool for authentication
        user_pool = cognito.UserPool(
            self,
            "MedConnectUserPool",
            self_sign_up_enabled=False,
            auto_verify=cognito.AutoVerify(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=True),
                given_name=cognito.StandardAttribute(required=True, mutable=True),
                family_name=cognito.StandardAttribute(required=True, mutable=True),
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            removal_policy=cognito.RemovalPolicy.RETAIN,
        )
        
        # Create User Pool Client
        user_pool_client = user_pool.add_client(
            "MedConnectUserPoolClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    implicit_code_grant=True,
                    authorization_code_grant=True,
                ),
                scopes=[cognito.OAuthScope.EMAIL, cognito.OAuthScope.OPENID, cognito.OAuthScope.PROFILE],
                callback_urls=["https://example.com/callback"],
                logout_urls=["https://example.com/logout"],
            ),
        )
        
        # Create API Gateway with Cognito Authorizer
        api = apigateway.RestApi(
            self,
            "MedConnectApi",
            rest_api_name="MedConnect API",
            description="API for MedConnect healthcare data integration platform",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization", "X-Api-Key"],
            ),
        )
        
        # Create Cognito Authorizer
        authorizer = apigateway.CognitoUserPoolsAuthorizer(
            self,
            "MedConnectAuthorizer",
            cognito_user_pools=[user_pool],
        )
        
        # Create API resources and methods if Lambda functions are provided
        if lambda_functions:
            # FHIR API
            fhir_resource = api.root.add_resource("fhir")
            
            # Patient resource
            patient_resource = fhir_resource.add_resource("Patient")
            patient_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            patient_resource.add_method(
                "POST",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            patient_id_resource = patient_resource.add_resource("{id}")
            patient_id_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            patient_id_resource.add_method(
                "PUT",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            # Observation resource
            observation_resource = fhir_resource.add_resource("Observation")
            observation_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            observation_resource.add_method(
                "POST",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            observation_id_resource = observation_resource.add_resource("{id}")
            observation_id_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.fhir_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            # Analytics API
            analytics_resource = api.root.add_resource("analytics")
            
            # Patient analytics
            patient_analytics_resource = analytics_resource.add_resource("patient")
            patient_analytics_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.analytics_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            patient_analytics_id_resource = patient_analytics_resource.add_resource("{id}")
            patient_analytics_id_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.analytics_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            # Population analytics
            population_analytics_resource = analytics_resource.add_resource("population")
            population_analytics_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.analytics_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            # ML API
            ml_resource = api.root.add_resource("ml")
            
            # Predictions
            predictions_resource = ml_resource.add_resource("predictions")
            predictions_resource.add_method(
                "POST",
                apigateway.LambdaIntegration(lambda_functions.ml_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            predictions_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.ml_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
            
            prediction_id_resource = predictions_resource.add_resource("{id}")
            prediction_id_resource.add_method(
                "GET",
                apigateway.LambdaIntegration(lambda_functions.ml_lambda),
                authorizer=authorizer,
                authorization_type=apigateway.AuthorizationType.COGNITO,
            )
        
        # Export API endpoint
        self.api_endpoint = api.url 