provider "aws" {
  region = "us-east-1"
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

  tags = {
    Name = "FruitStoreSG"
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
      "export DEBIAN_FRONTEND=noninteractive",

      # Disable interactive restart prompts
      "echo '\\$nrconf{restart} = \"a\";' | sudo tee /etc/needrestart/needrestart.conf",

      # Standard install commands
      "sudo apt-get update -y",
      "sudo apt-get install -y software-properties-common",
      "sudo add-apt-repository -y universe",
      "sudo apt-get update -y",
      "sudo apt-get install -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' python3-pip git postgresql postgresql-contrib",

      # Clone the repo
      "git clone https://github.com/gopi-maganti/fruitstore-flask.git",
      "cd fruitstore-flask",

      # Export env vars from .env
      "export $(grep -v '^#' .env | xargs)",

      # Use grep to extract .env variables
      "DB_USER=$(grep DB_USER .env | cut -d '=' -f2 | xargs)",
      "DB_PASSWORD=$(grep DB_PASSWORD .env | cut -d '=' -f2 | xargs)",
      "DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2 | xargs)",

      # Create DB user and DB
      "sudo -u postgres psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';\"",
      "sudo -u postgres psql -c \"CREATE DATABASE $DB_NAME;\"",
      "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;\"",

      # Install Python requirements
      "pip3 install -r requirements.txt",
      "pip3 install python-dotenv",

      # Launch Flask
      "FLASK_RUN_HOST=0.0.0.0 FLASK_RUN_PORT=5000 nohup python3 run.py > output.log 2>&1 &"
    ]
  }

  tags = {
    Name = "FruitStoreInstance"
  }
}
