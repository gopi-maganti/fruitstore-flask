
resource "aws_secretsmanager_secret" "db_secret" {
  name        = "fruitstore-db-secret"
  description = "Database credentials for Fruitstore"
}

resource "aws_secretsmanager_secret_version" "db_secret_version" {
  secret_id     = aws_secretsmanager_secret.db_secret.id
  secret_string = jsonencode({
    username = "fruituser",
    password = "SuperSecurePass123",
    engine   = "postgres",
    host     = "fruitstore-db.xxxxxx.us-east-1.rds.amazonaws.com",
    port     = 5432,
    dbname   = "fruitstore"
  })
}

output "secret_arn" {
  value = aws_secretsmanager_secret.db_secret.arn
}
