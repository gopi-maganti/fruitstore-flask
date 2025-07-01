provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "fruitstore_vpc" {
  cidr_block = var.vpc_cidr
}

resource "aws_key_pair" "fruitstore_key_pair" {
  key_name   = "fruitstore_key"
  public_key = file("/Users/gopikrishnamaganti/.ssh/id_rsa.pub")
}

resource "aws_subnet" "fruitstore_subnet" {
  vpc_id            = aws_vpc.fruitstore_vpc.id
  cidr_block        = "10.0.0.0/24"
  availability_zone = "us-east-1a"
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
}

resource "aws_instance" "fruitstore_instance" {
  ami = "ami-08c40ec9ead489470"
  instance_type = "t2.micro"
  key_name      = aws_key_pair.fruitstore_key_pair.key_name
  subnet_id     = aws_subnet.fruitstore_subnet.id
  security_groups = [aws_security_group.fruitstore_sg.id]

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = "${file("/Users/gopikrishnamaganti/.ssh/id_rsa")}"
    host        = self.public_ip
    agent       = true
  }
  provisioner "file" {
    source      = "/Users/gopikrishnamaganti/Desktop/Projects/fruitstore-flask/.env"
    destination = "/home/ubuntu/.env"
  }
  provisioner "remote-exec" {
    inline = [
      "sudo apt update -y",
      "sudo apt install -y python3-pip git postgresql postgresql-contrib",
      "set -o allexport && source /home/ubuntu/.env && set +o allexport",
      "git clone https://github.com/gopi-maganti/fruitstore-flask.git",
      "cd fruitstore-flask",
      
      # Setup PostgreSQL
      "sudo systemctl start postgresql",
      "sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\" -c \"CREATE DATABASE $DB_NAME;\" -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"",

      # Install Python dependencies and run app
      "pip3 install -r requirements.txt",
      "python3 run.py"
    ]
  }
}
