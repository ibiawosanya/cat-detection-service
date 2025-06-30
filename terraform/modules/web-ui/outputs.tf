output "s3_bucket_name" {
  description = "Name of the S3 bucket for web UI"
  value       = aws_s3_bucket.web_ui.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket for web UI"
  value       = aws_s3_bucket.web_ui.arn
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.web_ui.id
}

output "cloudfront_url" {
  description = "URL of the CloudFront distribution"
  value       = "https://${aws_cloudfront_distribution.web_ui.domain_name}"
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.web_ui.domain_name
}