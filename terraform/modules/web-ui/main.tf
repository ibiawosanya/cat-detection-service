# S3 Bucket for Web UI
resource "aws_s3_bucket" "web_ui" {
  bucket = "${var.environment}-${var.project}-web-ui-${random_id.bucket_suffix.hex}"
}

resource "aws_s3_bucket_public_access_block" "web_ui" {
  bucket = aws_s3_bucket.web_ui.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "web_ui" {
  bucket = aws_s3_bucket.web_ui.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.web_ui.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.web_ui.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.web_ui]
}

resource "aws_s3_bucket_website_configuration" "web_ui" {
  bucket = aws_s3_bucket.web_ui.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# CloudFront Distribution
resource "aws_cloudfront_origin_access_identity" "web_ui" {
  comment = "${var.environment} ${var.project} OAI"
}

resource "aws_cloudfront_distribution" "web_ui" {
  origin {
    domain_name = aws_s3_bucket.web_ui.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.web_ui.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.web_ui.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.web_ui.id}"
    compress               = var.enable_compression

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  price_class = var.price_class

  tags = {
    Environment = var.environment
    Project     = var.project
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}