resource "aws_secretsmanager_secret" "db_secret" {
  name        = "fruitstore-db-secret-v9"
  description = "PostgreSQL credentials for FruitStore app"
}

resource "aws_secretsmanager_secret_version" "db_secret_version" {
  secret_id     = aws_secretsmanager_secret.db_secret.id
  secret_string = jsonencode({
    username = "fruituser",
    password = "SuperSecurePass123",
    engine   = "postgres"
    host     = "fruitstore-cluster.cluster-c69cq4mcm794.us-east-1.rds.amazonaws.com"
    port     = 5432
    dbname   = "fruitstore"
  })
}
