import pulumi
import pulumi_aws as aws
import json
from pathlib import Path

# Get configuration
config = pulumi.Config()
environment = config.get("environment") or "dev"
lambda_memory = config.get_int("lambda-memory") or 512
lambda_timeout = config.get_int("lambda-timeout") or 30

# Get current AWS account and region
current = aws.get_caller_identity()
region = aws.get_region()

# Create S3 bucket for storing uploaded images
images_bucket = aws.s3.Bucket(
    "cat-detector-images",
    bucket=f"cat-detector-images-{current.account_id}-{region.name}",
    cors_rules=[
        aws.s3.BucketCorsRuleArgs(
            allowed_methods=["GET", "PUT", "POST", "DELETE"],
            allowed_origins=["*"],
            allowed_headers=["*"],
            max_age_seconds=3000,
        )
    ],
    tags={
        "Environment": environment,
        "Project": "cat-detector",
        "Purpose": "image-storage"
    }
)

# FIXED: Create S3 bucket for hosting web frontend (NO website hosting)
web_bucket = aws.s3.Bucket(
    "cat-detector-web",
    bucket=f"cat-detector-web-{current.account_id}-{region.name}",
    # REMOVED: website configuration - using OAC instead
    tags={
        "Environment": environment,
        "Project": "cat-detector",
        "Purpose": "web-hosting"
    }
)

# FIXED: Block ALL public access (required for OAC security)
web_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "web-bucket-public-access-block",
    bucket=web_bucket.id,
    block_public_acls=True,
    block_public_policy=True,  
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# FIXED: Create Origin Access Control (OAC) - modern AWS best practice
origin_access_control = aws.cloudfront.OriginAccessControl(
    "web-oac",
    name="cat-detector-web-oac",
    description="OAC for cat detector web bucket",
    origin_access_control_origin_type="s3",
    signing_behavior="always",  # Always sign requests for security
    signing_protocol="sigv4"
)

# Create DynamoDB table for storing scan results
results_table = aws.dynamodb.Table(
    "cat-detector-results",
    name="cat-detector-results",
    billing_mode="PAY_PER_REQUEST",
    hash_key="scanId",
    attributes=[
        aws.dynamodb.TableAttributeArgs(
            name="scanId",
            type="S",
        ),
    ],
    point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(
        enabled=True,
    ),
    tags={
        "Environment": environment,
        "Project": "cat-detector",
        "Purpose": "results-storage"
    }
)

# Create IAM role for Lambda functions
lambda_role = aws.iam.Role(
    "cat-detector-lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com",
                },
            }
        ],
    }),
    managed_policy_arns=[
        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    ],
    tags={
        "Environment": environment,
        "Project": "cat-detector"
    }
)

# Create IAM policy for Lambda functions
lambda_policy = aws.iam.RolePolicy(
    "cat-detector-lambda-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(
        images_bucket.arn,
        results_table.arn
    ).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                    ],
                    "Resource": f"{args[0]}/*",
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                    ],
                    "Resource": args[1],
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "rekognition:DetectLabels",
                        "rekognition:DetectText",
                    ],
                    "Resource": "*",
                },
            ],
        })
    ),
)

# Create Lambda function for handling uploads
upload_lambda = aws.lambda_.Function(
    "upload-function",
    name=f"cat-detector-upload-{environment}",
    runtime=aws.lambda_.Runtime.PYTHON3D9,
    handler="upload_handler.lambda_handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./src/lambdas")
    }),
    role=lambda_role.arn,
    timeout=lambda_timeout,
    memory_size=lambda_memory,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "IMAGES_BUCKET": images_bucket.bucket,
            "RESULTS_TABLE": results_table.name,
            "ENVIRONMENT": environment,
        }
    ),
    tags={
        "Environment": environment,
        "Project": "cat-detector",
        "Function": "upload"
    }
)

# Create Lambda function for processing images
process_lambda = aws.lambda_.Function(
    "process-function",
    name=f"cat-detector-process-{environment}",
    runtime=aws.lambda_.Runtime.PYTHON3D9,
    handler="process_handler.lambda_handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./src/lambdas")
    }),
    role=lambda_role.arn,
    timeout=60,
    memory_size=1024,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "IMAGES_BUCKET": images_bucket.bucket,
            "RESULTS_TABLE": results_table.name,
            "ENVIRONMENT": environment,
        }
    ),
    tags={
        "Environment": environment,
        "Project": "cat-detector",
        "Function": "process"
    }
)

# Create Lambda function for status queries
status_lambda = aws.lambda_.Function(
    "status-function",
    name=f"cat-detector-status-{environment}",
    runtime=aws.lambda_.Runtime.PYTHON3D9,
    handler="status_handler.lambda_handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive("./src/lambdas")
    }),
    role=lambda_role.arn,
    timeout=lambda_timeout,
    memory_size=lambda_memory,
    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "RESULTS_TABLE": results_table.name,
            "ENVIRONMENT": environment,
        }
    ),
    tags={
        "Environment": environment,
        "Project": "cat-detector",
        "Function": "status"
    }
)

# Create S3 bucket notification to trigger processing
bucket_notification = aws.s3.BucketNotification(
    "bucket-notification",
    bucket=images_bucket.id,
    lambda_functions=[
        aws.s3.BucketNotificationLambdaFunctionArgs(
            lambda_function_arn=process_lambda.arn,
            events=["s3:ObjectCreated:*"],
            filter_prefix="uploads/",
        )
    ],
)

# Grant S3 permission to invoke the processing Lambda
lambda_permission = aws.lambda_.Permission(
    "allow-s3-invoke",
    statement_id="AllowExecutionFromS3Bucket",
    action="lambda:InvokeFunction",
    function=process_lambda.name,
    principal="s3.amazonaws.com",
    source_arn=images_bucket.arn,
)

# Create API Gateway
api = aws.apigateway.RestApi(
    "cat-detector-api",
    name=f"cat-detector-api-{environment}",
    description="API for Cat Detector service",
    endpoint_configuration=aws.apigateway.RestApiEndpointConfigurationArgs(
        types="REGIONAL",
    ),
    tags={
        "Environment": environment,
        "Project": "cat-detector"
    }
)

# Create API Gateway resources and methods
upload_resource = aws.apigateway.Resource(
    "upload-resource",
    rest_api=api.id,
    parent_id=api.root_resource_id,
    path_part="upload",
)

status_resource = aws.apigateway.Resource(
    "status-resource",
    rest_api=api.id,
    parent_id=api.root_resource_id,
    path_part="status",
)

status_id_resource = aws.apigateway.Resource(
    "status-id-resource",
    rest_api=api.id,
    parent_id=status_resource.id,
    path_part="{scanId}",
)

debug_resource = aws.apigateway.Resource(
    "debug-resource",
    rest_api=api.id,
    parent_id=api.root_resource_id,
    path_part="debug",
)

debug_id_resource = aws.apigateway.Resource(
    "debug-id-resource",
    rest_api=api.id,
    parent_id=debug_resource.id,
    path_part="{scanId}",
)

# Create API Gateway methods
upload_method = aws.apigateway.Method(
    "upload-method",
    rest_api=api.id,
    resource_id=upload_resource.id,
    http_method="POST",
    authorization="NONE",
)

status_method = aws.apigateway.Method(
    "status-method",
    rest_api=api.id,
    resource_id=status_id_resource.id,
    http_method="GET",
    authorization="NONE",
)

debug_method = aws.apigateway.Method(
    "debug-method",
    rest_api=api.id,
    resource_id=debug_id_resource.id,
    http_method="GET",
    authorization="NONE",
)

# Create API Gateway integrations
upload_integration = aws.apigateway.Integration(
    "upload-integration",
    rest_api=api.id,
    resource_id=upload_resource.id,
    http_method=upload_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=upload_lambda.invoke_arn,
)

status_integration = aws.apigateway.Integration(
    "status-integration",
    rest_api=api.id,
    resource_id=status_id_resource.id,
    http_method=status_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=status_lambda.invoke_arn,
)

debug_integration = aws.apigateway.Integration(
    "debug-integration",
    rest_api=api.id,
    resource_id=debug_id_resource.id,
    http_method=debug_method.http_method,
    integration_http_method="POST",
    type="AWS_PROXY",
    uri=status_lambda.invoke_arn,
)

# Create API Gateway deployment
deployment = aws.apigateway.Deployment(
    "api-deployment",
    rest_api=api.id,
    opts=pulumi.ResourceOptions(
        depends_on=[
            upload_integration,
            status_integration,
            debug_integration,
        ]
    ),
)

# Create API Gateway Stage (fixes deprecation warning)
api_stage = aws.apigateway.Stage(
    "api-stage",
    deployment=deployment.id,
    rest_api=api.id,
    stage_name=environment,
    tags={
        "Environment": environment,
        "Project": "cat-detector"
    }
)

# Grant API Gateway permission to invoke Lambda functions
upload_api_permission = aws.lambda_.Permission(
    "upload-api-permission",
    statement_id="AllowExecutionFromAPIGateway",
    action="lambda:InvokeFunction",
    function=upload_lambda.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"),
)

status_api_permission = aws.lambda_.Permission(
    "status-api-permission",
    statement_id="AllowExecutionFromAPIGateway",
    action="lambda:InvokeFunction",
    function=status_lambda.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(api.execution_arn, "/*/*"),
)

# FIXED: Create CloudFront distribution with proper OAC
distribution = aws.cloudfront.Distribution(
    "web-distribution",
    origins=[
        aws.cloudfront.DistributionOriginArgs(
            domain_name=web_bucket.bucket_regional_domain_name,
            origin_id="S3-Web-OAC",
            origin_access_control_id=origin_access_control.id,  # Use OAC
            # REMOVED: custom_origin_config - using S3 REST API endpoint instead
        )
    ],
    enabled=True,
    is_ipv6_enabled=True,
    default_root_object="index.html",
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=["GET", "HEAD", "OPTIONS"],  # Reduced for security
        cached_methods=["GET", "HEAD"],
        target_origin_id="S3-Web-OAC",
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none",
            ),
        ),
        viewer_protocol_policy="redirect-to-https",
        min_ttl=0,
        default_ttl=3600,
        max_ttl=86400,
        compress=True,  # Enable compression
    ),
    # FIXED: Custom error responses for SPA routing
    custom_error_responses=[
        aws.cloudfront.DistributionCustomErrorResponseArgs(
            error_code=403,  # Handle OAC Access Denied as index.html
            response_code=200,
            response_page_path="/index.html",
            error_caching_min_ttl=300
        ),
        aws.cloudfront.DistributionCustomErrorResponseArgs(
            error_code=404,
            response_code=200,
            response_page_path="/index.html",
            error_caching_min_ttl=300
        )
    ],
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ),
    tags={
        "Environment": environment,
        "Project": "cat-detector"
    }
)

# FIXED: S3 bucket policy for OAC (CloudFront service principal)
web_bucket_policy = aws.s3.BucketPolicy(
    "web-bucket-oac-policy",
    bucket=web_bucket.id,
    policy=pulumi.Output.all(
        web_bucket.arn,
        distribution.arn
    ).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudFrontServicePrincipal",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudfront.amazonaws.com"
                    },
                    "Action": "s3:GetObject",
                    "Resource": f"{args[0]}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": args[1]
                        }
                    }
                }
            ]
        })
    ),
    opts=pulumi.ResourceOptions(depends_on=[web_bucket_public_access_block])
)

# OPTION 2: CLEAN External File Approach - Read HTML from external file and inject API URL
def create_updated_html(api_url_value):
    try:
        # Read the HTML template file
        html_path = Path("src/web/index.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Replace the placeholder with actual API URL
        updated_html = html_content.replace('YOUR_API_URL_HERE', api_url_value)
        
        return updated_html
    except FileNotFoundError:
        # Fallback: if file doesn't exist, create minimal working HTML
        print("⚠️  WARNING: src/web/index.html not found. Creating minimal fallback HTML.")
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cat Detector - Minimal</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 2rem auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            text-align: center;
        }}
        .container {{
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 2rem;
        }}
        .error {{
            background: rgba(255, 0, 0, 0.2);
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🐱 Cat Detector</h1>
        <div class="error">
            <h3>⚠️ Setup Required</h3>
            <p>The main HTML file is missing. Please create <code>src/web/index.html</code> for full functionality.</p>
        </div>
        <p><strong>API URL:</strong> {api_url_value}</p>
        <p>This is a minimal fallback interface.</p>
    </div>
    <script>
        const API_BASE_URL = '{api_url_value}';
        console.log('Cat Detector API configured:', API_BASE_URL);
        console.warn('Using fallback HTML. Create src/web/index.html for full functionality.');
    </script>
</body>
</html>'''
    except Exception as e:
        print(f"❌ ERROR reading HTML file: {e}")
        # Ultra-minimal fallback
        return f'''<!DOCTYPE html>
<html>
<head><title>Cat Detector - Error</title></head>
<body>
    <h1>Cat Detector</h1>
    <p>Error loading HTML template: {str(e)}</p>
    <p>API: {api_url_value}</p>
    <script>const API_BASE_URL = '{api_url_value}';</script>
</body>
</html>'''

# Generate API URL for HTML injection
api_url = pulumi.Output.concat("https://", api.id, ".execute-api.", region.name, ".amazonaws.com/", environment)

# Upload the updated HTML file (reads from external file)
index_html_object = aws.s3.BucketObject(
    "index-html",
    bucket=web_bucket.id,
    key="index.html",
    content=api_url.apply(create_updated_html),
    content_type="text/html",
    cache_control="no-cache, no-store, must-revalidate",
    opts=pulumi.ResourceOptions(depends_on=[web_bucket_policy])
)

# Export important values
pulumi.export("api_url", api_url)
pulumi.export("website_url", pulumi.Output.concat("https://", distribution.domain_name))
pulumi.export("images_bucket", images_bucket.bucket)
pulumi.export("web_bucket", web_bucket.bucket)
pulumi.export("results_table", results_table.name)
pulumi.export("environment", environment)
pulumi.export("upload_lambda_name", upload_lambda.name)
pulumi.export("process_lambda_name", process_lambda.name)
pulumi.export("status_lambda_name", status_lambda.name)
pulumi.export("region", region.name)
pulumi.export("account_id", current.account_id)
pulumi.export("distribution_id", distribution.id)
pulumi.export("origin_access_control_id", origin_access_control.id)