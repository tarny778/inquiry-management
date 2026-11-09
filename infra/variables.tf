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
