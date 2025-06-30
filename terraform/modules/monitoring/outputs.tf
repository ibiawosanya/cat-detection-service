output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cat_detection.dashboard_name}"
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = var.enable_sns_alerts ? aws_sns_topic.alerts[0].arn : null
}

output "log_group_names" {
  description = "Names of the CloudWatch log groups"
  value = [
    aws_cloudwatch_log_group.upload_logs.name,
    aws_cloudwatch_log_group.process_logs.name,
    aws_cloudwatch_log_group.status_logs.name
  ]
}
