# Fetch Ubuntu-jammy-22.04 from AMI registry
data "aws_ami" "ubuntu" {
  most_recent = true
  owners = [ "099720109477" ] # Canonical

  filter {
    name = "name"
    values = [ "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" ] 
  }

  filter {
    name = "virtualization-type"
    values = [ "hvm" ]
  }
}

# "Firewall" rules
resource "aws_security_group" "api_sg" {
  name = "fraud-api-security-group"
  description = "Allow HTTP, SSH and Grafan traffic"

  # Nginx LB
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  # SSH
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  # Grafana
  ingress {
    from_port = 3000
    to_port = 3000
    protocol = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  # Allow internet connectivity form VM
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = [ "0.0.0.0/0" ]
  }
}

resource "aws_key_pair" "deployer" {
  key_name   = "fraud-api-deployer-key"
  public_key = file(pathexpand("~/.ssh/fraud_api_aws.pub"))
}

resource "aws_instance" "api_server" {
  ami = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name = aws_key_pair.deployer.key_name
  vpc_security_group_ids = [ aws_security_group.api_sg.id ]

  root_block_device {
    volume_size = 25
    volume_type = "gp3"
    delete_on_termination = true
  }

  user_data = <<-EOF
              #!/bin/bash
              export DEBIAN_FRONTEND=noninteractive

              # wait for system apt/dpkg locks to clear
              while systemctl is-active --quiet daily-apt-upgrade.service; do
                sleep 5
              done

              # create 2GB swap file
              if [ ! -f /swapfile ]; then
                fallocate -l 2G /swapfile
                chmod 600 /swapfile
                mkswap /swapfile
                swapon /swapfile
                echo '/swapfile none swap sw 0 0' >> /etc/fstab
              fi

              # install Docker
              apt-get update -y
              apt-get install -y ca-certificates curl gnupg

              . /etc/os-release
              CODENAME=$VERSION_CODENAME

              mkdir -p /etc/apt/keyrings

              curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor --yes -o /etc/apt/keyrings/docker.gpg

              echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $CODENAME stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

              apt-get update -y
              apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

              # enable Docker & permit 'ubuntu' user
              usermod -aG docker ubuntu
              systemctl enable docker
              systemctl start docker

              # create /app
              mkdir -p /home/ubuntu/app
              chown -R ubuntu:ubuntu /home/ubuntu/app
              EOF
              
  tags = {
    Name = "Fraud-Detection-API-Server"
  }
}

output "public_ip" {
  value = aws_instance.api_server.public_ip
  description = "Public IP address of the EC2 instance"
}
