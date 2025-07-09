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

resource "aws_s3_bucket" "fruitstore_bucket" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = "FruitStore Image Uploads"
  }
}

resource "aws_cloudwatch_log_group" "secret_access_logs" {
  name              = "/aws/fruitstore/secret_access"
  retention_in_days = 14
}

resource "aws_vpc_dhcp_options" "fruitstore_dhcp" {
  domain_name         = "ec2.internal"
  domain_name_servers = ["AmazonProvidedDNS"]
}

resource "aws_vpc_dhcp_options_association" "fruitstore_dhcp_assoc" {
  vpc_id          = aws_vpc.fruitstore_vpc.id
  dhcp_options_id = aws_vpc_dhcp_options.fruitstore_dhcp.id
}

resource "aws_vpc" "fruitstore_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

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

resource "aws_subnet" "fruitstore_subnet_1a" {
  vpc_id            = aws_vpc.fruitstore_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "fruitstore_subnet_1b" {
  vpc_id            = aws_vpc.fruitstore_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  map_public_ip_on_launch = true
}

resource "aws_db_subnet_group" "fruitstore_subnet_group" {
  name       = "fruitstore-db-subnet-group"
  subnet_ids = [
    aws_subnet.fruitstore_subnet_1a.id,
    aws_subnet.fruitstore_subnet_1b.id
  ]

  tags = {
    Name = "FruitStoreDBSubnetGroup"
  }
}

resource "aws_rds_cluster" "fruitstore_cluster" {
  cluster_identifier      = "fruitstore-cluster"
  engine                  = "aurora-postgresql"
  engine_mode             = "provisioned"
  master_username         = var.db_username
  master_password         = var.db_password
  database_name           = var.db_name
  db_subnet_group_name    = aws_db_subnet_group.fruitstore_subnet_group.name
  vpc_security_group_ids  = [aws_security_group.fruitstore_sg.id]
  skip_final_snapshot     = true
}

resource "aws_rds_cluster_instance" "fruitstore_instance" {
  identifier              = "fruitstore-instance-1"
  cluster_identifier      = aws_rds_cluster.fruitstore_cluster.id
  instance_class          = "db.t3.medium"
  engine                  = "aurora-postgresql"
  publicly_accessible     = true
  db_subnet_group_name    = aws_db_subnet_group.fruitstore_subnet_group.name
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

resource "aws_route_table_association" "fruitstore_RTA_1a" {
  subnet_id      = aws_subnet.fruitstore_subnet_1a.id
  route_table_id = aws_route_table.fruitstore_RT.id
}

resource "aws_route_table_association" "fruitstore_RTA_1b" {
  subnet_id      = aws_subnet.fruitstore_subnet_1b.id
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
  ingress {
    description = "Allow PostgreSQL from EC2"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
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

resource "aws_instance" "fruitstore_instance" {
  ami                         = var.ami_id
  instance_type               = "t2.micro"
  key_name                    = aws_key_pair.fruitstore_key_pair.key_name
  subnet_id                   = aws_subnet.fruitstore_subnet_1a.id
  vpc_security_group_ids      = [aws_security_group.fruitstore_sg.id]
  iam_instance_profile        = aws_iam_instance_profile.fruitstore_profile.name
  associate_public_ip_address = true

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.private_key_path)
    host        = self.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get install -y python3-pip git",

      # Clone repo
      "git clone https://github.com/gopi-maganti/fruitstore-flask.git",
      "cd fruitstore-flask",

      # Install dependencies
      "pip3 install --user -r requirements.txt",

      # Ensure .env exists or handle securely
      "echo 'USE_AWS_SECRET=true' > .env",
      "echo 'AWS_SECRET_NAME=fruitstore-db-secret-v9' >> .env",
      "echo 'AWS_REGION=us-east-1' >> .env",
      "echo 'S3_BUCKET_NAME=fruitstore-image-uploads' >> .env",

      # Export manually if needed
      "export USE_AWS_SECRET=true",
      "export AWS_SECRET_NAME=fruitstore-db-secret-v9",
      "export AWS_REGION=us-east-1",
      "export S3_BUCKET_NAME=fruitstore-image-uploads",

      # Run Flask app in background
      "nohup python3 run.py > app.log 2>&1 &"
    ]
  }

  tags = {
    Name = "FruitStoreEC2"
  }
}
