#!/usr/bin/env python3
"""
Deploy Cognito CloudFormation stack with best practices.
"""

import boto3
import json
import sys
import time
from botocore.exceptions import ClientError

def deploy_cognito_stack(
    stack_name: str = "fastapi-cognito-stack",
    environment: str = "dev",
    project_name: str = "fastapi-auth",
    region: str = "us-east-1"
):
    """Deploy Cognito CloudFormation stack."""
    
    cf_client = boto3.client('cloudformation', region_name=region)
    
    # Read CloudFormation template
    try:
        with open('infrastructure/cognito-stack.yaml', 'r') as f:
            template_body = f.read()
    except FileNotFoundError:
        print("❌ CloudFormation template not found at infrastructure/cognito-stack.yaml")
        return False
    
    parameters = [
        {
            'ParameterKey': 'Environment',
            'ParameterValue': environment
        },
        {
            'ParameterKey': 'ProjectName',
            'ParameterValue': project_name
        }
    ]
    
    try:
        # Check if stack exists
        try:
            stack_info = cf_client.describe_stacks(StackName=stack_name)
            stack_status = stack_info['Stacks'][0]['StackStatus']
            
            # Handle different stack states
            if stack_status in ['ROLLBACK_COMPLETE', 'CREATE_FAILED']:
                print(f"🗑️ Stack in {stack_status} state - must delete and recreate")
                
                # Disable deletion protection if UserPool exists
                try:
                    resources = cf_client.describe_stack_resources(StackName=stack_name)
                    user_pool_id = None
                    for resource in resources['StackResources']:
                        if resource['LogicalResourceId'] == 'UserPool':
                            user_pool_id = resource['PhysicalResourceId']
                            break
                    
                    if user_pool_id:
                        cognito_client = boto3.client('cognito-idp', region_name=region)
                        cognito_client.update_user_pool(
                            UserPoolId=user_pool_id,
                            DeletionProtection='INACTIVE'
                        )
                        print("✅ UserPool deletion protection disabled")
                except Exception as e:
                    print(f"⚠️ Could not disable deletion protection: {e}")
                
                # Delete the stack
                print(f"🗑️ Deleting stack: {stack_name}")
                cf_client.delete_stack(StackName=stack_name)
                
                # Wait for deletion
                print("⏳ Waiting for stack deletion...")
                waiter = cf_client.get_waiter('stack_delete_complete')
                waiter.wait(
                    StackName=stack_name,
                    WaiterConfig={'Delay': 15, 'MaxAttempts': 20}
                )
                print("✅ Stack deleted successfully")
                stack_exists = False
                
            elif stack_status in ['ROLLBACK_FAILED', 'UPDATE_ROLLBACK_COMPLETE', 'DELETE_FAILED']:
                print(f"🔄 Updating failed stack: {stack_name} (Status: {stack_status})")
                stack_exists = True  # Treat as update operation
            else:
                stack_exists = True
                print(f"📝 Updating existing stack: {stack_name} (Status: {stack_status})")
                
        except ClientError as e:
            if 'does not exist' in str(e):
                stack_exists = False
                print(f"🆕 Creating new stack: {stack_name}")
            else:
                raise
        
        # Deploy stack
        if stack_exists:
            response = cf_client.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Project', 'Value': 'learning'},
                    {'Key': 'Environment', 'Value': environment},
                    {'Key': 'ManagedBy', 'Value': 'CloudFormation'}
                ]
            )
            operation = 'UPDATE'
        else:
            response = cf_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Project', 'Value': 'learning'},
                    {'Key': 'Environment', 'Value': environment},
                    {'Key': 'ManagedBy', 'Value': 'CloudFormation'}
                ]
            )
            operation = 'CREATE'
        
        print(f"🚀 Stack {operation.lower()} initiated...")
        
        # Wait for completion
        waiter_name = f'stack_{operation.lower()}_complete'
        waiter = cf_client.get_waiter(waiter_name)
        
        print("⏳ Waiting for stack operation to complete...")
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 15,
                'MaxAttempts': 40
            }
        )
        
        # Get stack outputs
        stack_info = cf_client.describe_stacks(StackName=stack_name)
        outputs = stack_info['Stacks'][0].get('Outputs', [])
        
        print(f"✅ Stack {operation.lower()} completed successfully!")
        print("\n📋 Stack Outputs:")
        
        env_vars = {}
        for output in outputs:
            key = output['OutputKey']
            value = output['OutputValue']
            print(f"   {key}: {value}")
            
            # Map to environment variables
            if key == 'UserPoolId':
                env_vars['COGNITO_USER_POOL_ID'] = value
            elif key == 'UserPoolClientId':
                env_vars['COGNITO_CLIENT_ID'] = value
            elif key == 'Region':
                env_vars['AWS_REGION'] = value
        
        # Update .env file
        if env_vars:
            update_env_file(env_vars)
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ValidationError' and 'No updates are to be performed' in str(e):
            print("ℹ️  No changes detected in stack")
            return True
        else:
            print(f"❌ CloudFormation error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def update_env_file(env_vars: dict):
    """Update .env file with CloudFormation outputs."""
    try:
        # Read current .env
        with open('.env', 'r') as f:
            lines = f.readlines()
        
        # Update values
        updated_lines = []
        updated_keys = set()
        
        for line in lines:
            if '=' in line and not line.strip().startswith('#'):
                key = line.split('=')[0].strip()
                if key in env_vars:
                    updated_lines.append(f"{key}={env_vars[key]}\n")
                    updated_keys.add(key)
                else:
                    updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        # Add missing keys
        for key, value in env_vars.items():
            if key not in updated_keys:
                updated_lines.append(f"{key}={value}\n")
        
        # Enable Cognito
        cognito_enabled = False
        for i, line in enumerate(updated_lines):
            if line.startswith('USE_COGNITO='):
                updated_lines[i] = 'USE_COGNITO=true\n'
                cognito_enabled = True
                break
        
        if not cognito_enabled:
            updated_lines.append('USE_COGNITO=true\n')
        
        # Write updated .env
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ Updated .env file with Cognito configuration")
        
    except Exception as e:
        print(f"⚠️  Could not update .env file: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Cognito CloudFormation stack')
    parser.add_argument('--stack-name', default='fastapi-cognito-stack', help='CloudFormation stack name')
    parser.add_argument('--environment', default='dev', choices=['dev', 'staging', 'prod'], help='Environment')
    parser.add_argument('--project-name', default='fastapi-auth', help='Project name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    print("🚀 Deploying Cognito CloudFormation stack...")
    print(f"   Stack Name: {args.stack_name}")
    print(f"   Environment: {args.environment}")
    print(f"   Project: {args.project_name}")
    print(f"   Region: {args.region}")
    print()
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"✅ AWS credentials configured for account: {identity['Account']}")
    except Exception as e:
        print(f"❌ AWS credentials not configured: {e}")
        print("Please run: aws configure")
        sys.exit(1)
    
    success = deploy_cognito_stack(
        stack_name=args.stack_name,
        environment=args.environment,
        project_name=args.project_name,
        region=args.region
    )
    
    if success:
        print("\n🎉 Deployment completed successfully!")
        print("   Your Cognito resources are now ready to use.")
        print("   The .env file has been updated with the new configuration.")
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)