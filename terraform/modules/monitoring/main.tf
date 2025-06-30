# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "upload_logs" {
  name              = "/aws/lambda/${var.environment}-cat-upload"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "process_logs" {
  name              = "/aws/lambda/${var.environment}-cat-process"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "status_logs" {
  name              = "/aws/lambda/${var.environment}-cat-status"
  retention_in_days = var.log_retention_days
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "upload_errors" {
  alarm_name          = "${var.environment}-cat-upload-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors upload lambda errors"
  
  dimensions = {
    FunctionName = "${var.environment}-cat-upload"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "process_duration" {
  alarm_name          = "${var.environment}-cat-process-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "45000"  # 45 seconds
  alarm_description   = "This metric monitors process lambda duration"
  
  dimensions = {
    FunctionName = "${var.environment}-cat-process"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "sqs_dlq_messages" {
  alarm_name          = "${var.environment}-sqs-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors DLQ messages"
  
  dimensions = {
    QueueName = "${var.environment}-cat-processing-dlq"
  }
  
  alarm_actions = [aws_sns_topic.alerts.arn]
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.environment}-cat-detection-alerts"
}

# Custom Metrics Dashboard
resource "aws_cloudwatch_dashboard" "cat_detection" {
  dashboard_name = "${var.environment}-cat-detection"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.environment}-cat-upload"],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Upload Lambda Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/SQS", "NumberOfMessagesSent", "QueueName", "${var.environment}-cat-processing-queue"],
            [".", "NumberOfMessagesReceived", ".", "."],
            [".", "ApproximateNumberOfVisibleMessages", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "SQS Processing Queue Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "${var.environment}-cat-scan-results"],
            [".", "ConsumedWriteCapacityUnits", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Metrics"
          period  = 300
        }
      }
    ]
  })
}