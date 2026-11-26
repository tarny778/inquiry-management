# DBバックアップ用バケット。状態ファイル用とは分離している(権限と保持期間が違うため)
resource "aws_s3_bucket" "backup" {
  # 名前は世界で一意である必要があるため、接頭辞だけ指定して、残りは自動で付く
  bucket_prefix = "inquiry-backup-"
}

# 公開アクセスをすべて遮断する
resource "aws_s3_bucket_public_access_block" "backup" {
  bucket                  = aws_s3_bucket.backup.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# 同じキーへの上書きでも、過去の版が残る
resource "aws_s3_bucket_versioning" "backup" {
  bucket = aws_s3_bucket.backup.id
  versioning_configuration {
    status = "Enabled"
  }
}

# サーバー側暗号化(SSE-S3)。新規バケットは既定で有効、というのが私の理解だが、
# 設定をコードに残す意味で明示する
resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# db/ 配下を30日で期限切れにする。EC2ロールに削除権限を持たせない代わりの世代管理
resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    id     = "expire-db-dumps"
    status = "Enabled"

    filter {
      prefix = "db/"
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

output "backup_bucket_name" {
  value = aws_s3_bucket.backup.bucket
}