locals {
  ecr_repositories = ["backend", "web"]
}

resource "aws_ecr_repository" "app" {
  for_each = toset(local.ecr_repositories)

  name                 = "inquiry-management/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true # terraform destroy で、イメージごと削除できる

  image_scanning_configuration {
    scan_on_push = true
  }
}

# 古いイメージを自動で消す(最新の5つだけ残す)
resource "aws_ecr_lifecycle_policy" "app" {
  for_each   = aws_ecr_repository.app
  repository = each.value.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the latest 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}