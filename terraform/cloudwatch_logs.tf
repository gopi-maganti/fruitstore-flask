
resource "aws_cloudwatch_log_group" "secret_access_logs" {
  name              = "/aws/fruitstore/secret_access"
  retention_in_days = 14
}
