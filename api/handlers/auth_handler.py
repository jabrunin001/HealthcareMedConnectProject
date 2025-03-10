import json
import os
import logging
from typing import Dict, Any, Optional
import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

# Configure logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger = Logger(service="auth-service", level=log_level)

# Initialize AWS clients
cognito_idp = boto3.client('cognito-idp')


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Get user information from Cognito token.
    
    Args:
        token: JWT token from Cognito
        
    Returns:
        User information or None if token is invalid
    """
    try:
        # In a real implementation, this would validate the JWT token
        # and extract user information from it
        # For simplicity, we're just returning a mock user
        return {
            "sub": "12345",
            "email": "user@example.com",
            "given_name": "John",
            "family_name": "Doe",
            "custom:role": "doctor"
        }
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return None


def authorize(token: str, resource_arn: str, action: str) -> bool:
    """
    Check if user is authorized to perform action on resource.
    
    Args:
        token: JWT token from Cognito
        resource_arn: ARN of the resource
        action: Action to perform
        
    Returns:
        True if authorized, False otherwise
    """
    user = get_user_from_token(token)
    if not user:
        return False
    
    # In a real implementation, this would check permissions
    # based on user roles and resource policies
    # For simplicity, we're just returning True
    return True


@logger.inject_lambda_context
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for authentication and authorization.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        API Gateway response
    """
    logger.info("Received authentication request")
    
    try:
        # Extract request details
        request_context = event.get("requestContext", {})
        http_method = request_context.get("httpMethod")
        resource = request_context.get("resourcePath")
        
        # Extract token from headers
        headers = event.get("headers", {})
        authorization = headers.get("Authorization", "")
        
        if not authorization.startswith("Bearer "):
            logger.warning("Missing or invalid Authorization header")
            return {
                "statusCode": 401,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "message": "Unauthorized - Missing or invalid token"
                })
            }
        
        token = authorization.replace("Bearer ", "")
        
        # Get user from token
        user = get_user_from_token(token)
        if not user:
            logger.warning("Invalid token")
            return {
                "statusCode": 401,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "message": "Unauthorized - Invalid token"
                })
            }
        
        # Check authorization
        resource_arn = f"arn:aws:execute-api:{os.environ.get('AWS_REGION')}:{os.environ.get('AWS_ACCOUNT_ID')}:{request_context.get('apiId')}/{request_context.get('stage')}/{http_method.lower()}{resource}"
        action = f"execute-api:{http_method.lower()}"
        
        if not authorize(token, resource_arn, action):
            logger.warning(f"User {user.get('sub')} not authorized for {action} on {resource_arn}")
            return {
                "statusCode": 403,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "message": "Forbidden - Insufficient permissions"
                })
            }
        
        # Return successful response with user context
        logger.info(f"User {user.get('sub')} authenticated and authorized")
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": "Authentication successful",
                "user": {
                    "id": user.get("sub"),
                    "email": user.get("email"),
                    "firstName": user.get("given_name"),
                    "lastName": user.get("family_name"),
                    "role": user.get("custom:role")
                }
            })
        }
    
    except Exception as e:
        logger.exception("Error processing authentication request")
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "message": f"Internal server error: {str(e)}"
            })
        } 