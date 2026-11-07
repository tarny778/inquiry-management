terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-1" # 東京

  default_tags {
    tags = {
      Project = "inquiry-management"
    }
  }
}

# 最新の Amazon Linux 2023 の AMI を取得する
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# 手元の公開鍵を登録する(秘密鍵は、登録しない)
resource "aws_key_pair" "this" {
  key_name   = "inquiry-key"
  public_key = var.ssh_public_key
}

resource "aws_security_group" "web" {
  name        = "inquiry-demo-sg"
  description = "SSH from my IP, HTTP/HTTPS from anywhere"

  ingress {
    description = "SSH (my IP only)"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip_cidr]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "this" {
  ami                         = data.aws_ssm_parameter.al2023.value
  instance_type               = var.instance_type
  key_name                    = aws_key_pair.this.key_name
  vpc_security_group_ids      = [aws_security_group.web.id]
  associate_public_ip_address = true

  # OSからシャットダウンしたとき、削除ではなく「停止」にする
  instance_initiated_shutdown_behavior = "stop"

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  # メタデータの取得に、トークンを必須にする(IMDSv2)
  metadata_options {
    http_tokens = "required"
  }

  user_data = templatefile("${path.module}/user_data.sh.tftpl", {
    shutdown_minutes = var.shutdown_minutes
  })

  tags = {
    Name = "inquiry-demo"
  }
  
  lifecycle {
    ignore_changes = [associate_public_ip_address]
  }
}
