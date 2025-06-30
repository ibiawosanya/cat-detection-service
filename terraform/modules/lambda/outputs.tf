output "upload_lambda_function_name" {
  description = "Name of the upload Lambda function"
  value       = aws_lambda_function.upload.function_name
}

output "upload_lambda_invoke_arn" {
  description = "Invoke ARN of the upload Lambda function"
  value       = aws_lambda_function.upload.invoke_arn
}

output "upload_lambda_arn" {
  description = "ARN of the upload Lambda function"
  value       = aws_lambda_function.upload.arn
}

output "process_lambda_function_name" {
  description = "Name of the process Lambda function"
  value       = aws_lambda_function.process.function_name
}

output "process_lambda_invoke_arn" {
  description = "Invoke ARN of the process Lambda function"
  value       = aws_lambda_function.process.invoke_arn
}

output "process_lambda_arn" {
  description = "ARN of the process Lambda function"
  value       = aws_lambda_function.process.arn
}

output "status_lambda_function_name" {
  description = "Name of the status Lambda function"
  value       = aws_lambda_function.status.function_name
}

output "status_lambda_invoke_arn" {
  description = "Invoke ARN of the status Lambda function"
  value       = aws_lambda_function.status.invoke_arn
}

output "status_lambda_arn" {
  description = "ARN of the status Lambda function"
  value       = aws_lambda_function.status.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
}