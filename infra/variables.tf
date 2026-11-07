variable "ssh_public_key" {
  description = "SSH の公開鍵(1行)。秘密鍵ではない"
  type        = string
}

variable "my_ip_cidr" {
  description = "SSH を許可する自分のIP(例: 203.0.113.5/32)"
  type        = string
}

variable "instance_type" {
  description = "EC2 のインスタンスタイプ"
  type        = string
  default     = "t3.small"
}

variable "shutdown_minutes" {
  description = "起動してから自動停止するまでの時間(分)"
  type        = number
  default     = 180
}
