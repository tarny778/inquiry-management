variable "github_oidc_subject" {
  description = "ロールを引き受けられる GitHub Actions の識別子(sub)。オーナーとリポジトリの数値IDを含む形式"
  type        = string
  default     = "repo:tarny778@160378227/inquiry-management@1408267514:ref:refs/heads/main"
}

# GitHub Actions を、AWS が信頼できる発行元として登録する
resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# このリポジトリの main ブランチからだけ、ロールを引き受けられる
data "aws_iam_policy_document" "github_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = [var.github_oidc_subject]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "inquiry-github-actions"
  assume_role_policy = data.aws_iam_policy_document.github_assume.json
}

# 許可するのは、この2つのリポジトリへの、イメージの保存だけ
data "aws_iam_policy_document" "github_ecr_push" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [for r in aws_ecr_repository.app : r.arn]
  }
}

resource "aws_iam_role_policy" "github_ecr_push" {
  name   = "ecr-push"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_ecr_push.json
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "github_ssm_deploy" {
  # 状態の確認(リソース指定ができない)
  statement {
    actions = [
      "ec2:DescribeInstances",
      "ssm:DescribeInstanceInformation",
    ]
    resources = ["*"]
  }

  # コマンドの送信: このEC2と、シェル実行のドキュメントに限定
  statement {
    actions = ["ssm:SendCommand"]
    resources = [
      "arn:aws:ec2:ap-northeast-1:${data.aws_caller_identity.current.account_id}:instance/${aws_instance.this.id}",
      "arn:aws:ssm:ap-northeast-1::document/AWS-RunShellScript",
    ]
  }

  # 実行結果の取得
  statement {
    actions = [
      "ssm:GetCommandInvocation",
      "ssm:ListCommandInvocations",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_ssm_deploy" {
  name   = "ssm-deploy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.github_ssm_deploy.json
}