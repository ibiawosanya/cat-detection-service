import pulumi
import os

def get_stack_config():
    """Get configuration based on current stack"""
    stack = pulumi.get_stack()
    
    # Base configuration
    config = {
        "lambda_memory": 512,
        "lambda_timeout": 30,
        "enable_xray": False,
        "enable_vpc": False,
    }
    
    # Environment-specific overrides
    if stack == "prod":
        config.update({
            "lambda_memory": 1024,
            "lambda_timeout": 60,
            "enable_xray": True,
            "enable_vpc": True,
            "enable_waf": True,
        })
    elif stack == "staging":
        config.update({
            "lambda_memory": 768,
            "lambda_timeout": 45,
            "enable_xray": True,
        })
    
    return config

def get_resource_tags(additional_tags=None):
    """Get standard resource tags"""
    stack = pulumi.get_stack()
    base_tags = {
        "Project": "cat-detector",
        "Environment": stack,
        "ManagedBy": "pulumi",
        "Owner": os.getenv("USER", "unknown"),
    }
    
    if additional_tags:
        base_tags.update(additional_tags)
    
    return base_tags
