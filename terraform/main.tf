provider "aws" {
  region = "us-east-1"
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

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
    host     = "localhost",
    port     = 5432,
    dbname   = "fruitstore"
  })
}

resource "aws_cloudwatch_log_group" "secret_access_logs" {
  name              = "/aws/fruitstore/secret_access"
  retention_in_days = 14
}

resource "aws_vpc" "fruitstore_vpc" {
  cidr_block = var.vpc_cidr
  tags = {
    Name = "FruitStoreVPC"
  }
}

resource "aws_key_pair" "fruitstore_key_pair" {
  key_name   = "fruitstore_key"
  public_key = file("/Users/gopikrishnamaganti/.ssh/id_rsa.pub")
  tags = {
    Name = "FruitStoreKeyPair"
  }
}

resource "aws_subnet" "fruitstore_subnet" {
  vpc_id                  = aws_vpc.fruitstore_vpc.id
  cidr_block              = "10.0.0.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_internet_gateway" "fruitstore_IGW" {
  vpc_id = aws_vpc.fruitstore_vpc.id
}

resource "aws_route_table" "fruitstore_RT" {
  vpc_id = aws_vpc.fruitstore_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.fruitstore_IGW.id
  }
}

resource "aws_route_table_association" "fruitstore_RTA" {
  subnet_id      = aws_subnet.fruitstore_subnet.id
  route_table_id = aws_route_table.fruitstore_RT.id
}

resource "aws_security_group" "fruitstore_sg" {
  name        = "fruitstore_sg"
  description = "Security group for FruitStore application"
  vpc_id      = aws_vpc.fruitstore_vpc.id

  ingress {
    description = "Allow HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Allow SSH traffic"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "Allow Flask app traffic"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "FruitStoreSG"
  }
}

resource "aws_iam_role" "fruitstore_role" {
  name = "fruitstore-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

resource "aws_iam_policy" "secrets_policy" {
  name   = "FruitstoreSecretsAccess"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue", "logs:PutLogEvents"],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_attach" {
  role       = aws_iam_role.fruitstore_role.name
  policy_arn = aws_iam_policy.secrets_policy.arn
}

resource "aws_iam_instance_profile" "fruitstore_profile" {
  name = "fruitstore-instance-profile"
  role = aws_iam_role.fruitstore_role.name
}
