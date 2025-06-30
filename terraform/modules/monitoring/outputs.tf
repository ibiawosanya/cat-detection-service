output "dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${aws_cloudwatch_dashboard.cat_detection.dashboard_name}"
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = var.enable_sns_alerts ? aws_sns_topic.alerts[0].arn : null
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.cat_detection.dashboard_name
}

output "alarm_names" {
  description = "Names of the CloudWatch alarms created"
  value = [
    aws_cloudwatch_metric_alarm.upload_errors.alarm_name,
    aws_cloudwatch_metric_alarm.process_errors.alarm_name,
    aws_cloudwatch_metric_alarm.status_errors.alarm_name,
    aws_cloudwatch_metric_alarm.process_duration.alarm_name,
    aws_cloudwatch_metric_alarm.sqs_dlq_messages.alarm_name,
    aws_cloudwatch_metric_alarm.upload_throttles.alarm_name
  ]
}