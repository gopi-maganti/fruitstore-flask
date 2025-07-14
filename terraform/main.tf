provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "fruitstore_bucket" {
  bucket = var.s3_bucket_name

  tags = {
    Name = "FruitStore Image Uploads"
  }
}

resource "aws_cloudwatch_log_group" "secret_access_logs" {
  name              = "/aws/fruitstore/secret_access"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "fruitstore_app_logs" {
  name              = "/aws/fruitstore/app"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "fruitstore_metrics" {
  name              = "/aws/fruitstore/metrics"
  retention_in_days = 14
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

resource "aws_security_group_rule" "postgres_from_same_sg" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.fruitstore_sg.id
  source_security_group_id = aws_security_group.fruitstore_sg.id
  description              = "Allow PostgreSQL from EC2 with same SG"
}

resource "aws_db_instance" "fruitstore_instance" {
  identifier              = "fruitstore-pg-instance"
  engine                  = "postgres"
  instance_class          = "db.t3.micro"
  username                = var.db_username
  password                = var.db_password
  db_name                 = var.db_name
  publicly_accessible     = true
  allocated_storage       = 20
  storage_type            = "gp2"
  db_subnet_group_name    = aws_db_subnet_group.fruitstore_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.fruitstore_sg.id]
  skip_final_snapshot     = true
  deletion_protection     = false
  multi_az                = false
}

resource "aws_key_pair" "fruitstore_key_pair" {
  key_name   = "fruitstore_key"
  public_key = file("/Users/gopikrishnamaganti/.ssh/id_rsa.pub")

  tags = {
    Name = "FruitStoreKeyPair"
  }
}

resource "aws_instance" "fruitstore_instance" {
  ami                         = var.ami_id
  instance_type               = "t2.micro"
  key_name                    = aws_key_pair.fruitstore_key_pair.key_name
  subnet_id                   = aws_subnet.fruitstore_subnet_1a.id
  vpc_security_group_ids      = [aws_security_group.fruitstore_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.fruitstore_profile.name
  associate_public_ip_address = true

  user_data = <<-EOF
              #!/bin/bash
              exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1
              sudo apt-get update -y
              sudo apt-get install -y python3-pip git awscli jq amazon-cloudwatch-agent
              cd /home/ubuntu
              git clone https://github.com/gopi-maganti/fruitstore-flask.git
              cd fruitstore-flask
              SECRET=$(aws secretsmanager get-secret-value --secret-id ${var.db_secret_name} --region us-east-1 --query SecretString --output text)
              echo "$SECRET" > db_secret.json
              export DB_HOST=$(jq -r .host db_secret.json)
              export DB_USER=$(jq -r .username db_secret.json)
              export DB_PASSWORD=$(jq -r .password db_secret.json)
              export DB_NAME=$(jq -r .dbname db_secret.json)
              export S3_BUCKET_NAME=fruitstore-image-uploads
              export USE_AWS_SECRET=true
              export AWS_SECRET_NAME=fruitstore-db-secret
              export AWS_REGION=us-east-1
              pip3 install -r requirements.txt
              nohup python3 run.py > app.log 2>&1 &

              cat <<EOT > /opt/aws/amazon-cloudwatch-agent/bin/config.json
              {
                "logs": {
                  "logs_collected": {
                    "files": {
                      "collect_list": [
                        {
                          "file_path": "/home/ubuntu/fruitstore-flask/app.log",
                          "log_group_name": "/aws/fruitstore/app",
                          "log_stream_name": "{instance_id}-app",
                          "timestamp_format": "%Y-%m-%d %H:%M:%S"
                        }
                      ]
                    }
                  }
                },
                "metrics": {
                  "append_dimensions": {
                    "InstanceId": "$${aws:InstanceId}"
                  },
                  "metrics_collected": {
                    "cpu": {
                      "measurement": ["cpu_usage_idle", "cpu_usage_iowait"],
                      "metrics_collection_interval": 60
                    },
                    "mem": {
                      "measurement": ["mem_used_percent"],
                      "metrics_collection_interval": 60
                    }
                  }
                }
              }
              EOT

              /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
                -a fetch-config \
                -m ec2 \
                -c file:/opt/aws/amazon-cloudwatch-agent/bin/config.json \
                -s
              EOF

  tags = {
    Name = "FruitStoreEC2"
  }
}
