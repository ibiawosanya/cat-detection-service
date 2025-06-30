# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "upload_logs" {
  name              = "/aws/lambda/${var.environment}-${var.project}-upload"
  retention_in_days = var.log_retention_days
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_log_group" "process_logs" {
  name              = "/aws/lambda/${var.environment}-${var.project}-process"
  retention_in_days = var.log_retention_days
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_log_group" "status_logs" {
  name              = "/aws/lambda/${var.environment}-${var.project}-status"
  retention_in_days = var.log_retention_days
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# SNS Topic for Alerts (conditional)
resource "aws_sns_topic" "alerts" {
  count = var.enable_sns_alerts ? 1 : 0
  name  = "${var.environment}-${var.project}-alerts"
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# SNS Topic Subscription (conditional)
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.enable_sns_alerts && var.alert_email != null ? 1 : 0
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "upload_errors" {
  alarm_name          = "${var.environment}-${var.project}-upload-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "This metric monitors upload lambda errors"
  
  dimensions = {
    FunctionName = "${var.environment}-${var.project}-upload"
  }
  
  alarm_actions = var.enable_sns_alerts ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_metric_alarm" "process_errors" {
  alarm_name          = "${var.environment}-${var.project}-process-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "This metric monitors process lambda errors"
  
  dimensions = {
    FunctionName = "${var.environment}-${var.project}-process"
  }
  
  alarm_actions = var.enable_sns_alerts ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_metric_alarm" "status_errors" {
  alarm_name          = "${var.environment}-${var.project}-status-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "This metric monitors status lambda errors"
  
  dimensions = {
    FunctionName = "${var.environment}-${var.project}-status"
  }
  
  alarm_actions = var.enable_sns_alerts ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_metric_alarm" "process_duration" {
  alarm_name          = "${var.environment}-${var.project}-process-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = var.duration_threshold
  alarm_description   = "This metric monitors process lambda duration"
  
  dimensions = {
    FunctionName = "${var.environment}-${var.project}-process"
  }
  
  alarm_actions = var.enable_sns_alerts ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_metric_alarm" "sqs_dlq_messages" {
  alarm_name          = "${var.environment}-${var.project}-sqs-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfVisibleMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors DLQ messages"
  
  dimensions = {
    QueueName = "${var.environment}-${var.project}-processing-dlq"
  }
  
  alarm_actions = var.enable_sns_alerts ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "aws_cloudwatch_metric_alarm" "upload_throttles" {
  alarm_name          = "${var.environment}-${var.project}-upload-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors upload lambda throttles"
  
  dimensions = {
    FunctionName = "${var.environment}-${var.project}-upload"
  }
  
  alarm_actions = var.enable_sns_alerts ? [aws_sns_topic.alerts[0].arn] : []
  
  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

# Custom Metrics Dashboard
resource "aws_cloudwatch_dashboard" "cat_detection" {
  dashboard_name = "${var.environment}-${var.project}"

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
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.environment}-${var.project}-upload"],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Upload Lambda Metrics"
          period  = 300
          stat    = "Sum"
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
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.environment}-${var.project}-process"],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Process Lambda Metrics"
          period  = 300
          stat    = "Sum"
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
            ["AWS/Lambda", "Invocations", "FunctionName", "${var.environment}-${var.project}-status"],
            [".", "Errors", ".", "."],
            [".", "Duration", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Status Lambda Metrics"
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/SQS", "NumberOfMessagesSent", "QueueName", "${var.environment}-${var.project}-processing-queue"],
            [".", "NumberOfMessagesReceived", ".", "."],
            [".", "ApproximateNumberOfVisibleMessages", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "SQS Processing Queue Metrics"
          period  = 300
          stat    = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 24
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfVisibleMessages", "QueueName", "${var.environment}-${var.project}-processing-dlq"]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Dead Letter Queue Messages"
          period  = 300
          stat    = "Maximum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 30
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "${var.environment}-${var.project}-scan-results"],
            [".", "ConsumedWriteCapacityUnits", ".", "."],
            [".", "ItemCount", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Table Metrics"
          period  = 300
          stat    = "Sum"
        }
      }
    ]
  })
}