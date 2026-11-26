data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = "inquiry-demo-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

# 段階4(SSM)用。先に付けておく
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# ECR pull用
data "aws_iam_policy_document" "ecr_pull" {
  statement {
    sid       = "EcrAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "EcrPull"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = [for r in aws_ecr_repository.app : r.arn]
  }
}

resource "aws_iam_role_policy" "ecr_pull" {
  name   = "ecr-pull"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.ecr_pull.json
}

# DBバックアップ用。書き込みと、復元のための読み取りだけを許可する(削除は許可しない)
data "aws_iam_policy_document" "s3_backup" {
  statement {
    sid       = "BackupObjects"
    actions   = ["s3:PutObject", "s3:GetObject"]
    resources = ["${aws_s3_bucket.backup.arn}/db/*"]
  }

  statement {
    sid       = "BackupList"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.backup.arn]
    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["db/*"]
    }
  }
}

resource "aws_iam_role_policy" "s3_backup" {
  name   = "s3-backup"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.s3_backup.json
}

resource "aws_iam_instance_profile" "ec2" {
  name = "inquiry-demo-ec2-profile"
  role = aws_iam_role.ec2.name
}