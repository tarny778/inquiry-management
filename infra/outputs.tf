output "instance_id" {
  value = aws_instance.this.id
}

output "public_ip" {
  value = aws_instance.this.public_ip
}

output "ssh_command" {
  value = "ssh -i ~/.ssh/inquiry-key.pem ec2-user@${aws_instance.this.public_ip}"
}
