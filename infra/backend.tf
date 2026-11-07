terraform {
  backend "s3" {
    bucket       = "inquiry-tfstate-84037c34"
    key          = "inquiry-demo/terraform.tfstate"
    region       = "ap-northeast-1"
    use_lockfile = true
  }
}