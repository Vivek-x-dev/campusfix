output "alb_dns_name" {
  description = "The DNS name of the Application Load Balancer"
  value       = aws_lb.alb.dns_name
}

output "ecr_frontend_repository_url" {
  description = "URL of the Frontend ECR repository"
  value       = aws_ecr_repository.frontend.repository_url
}

output "ecr_backend_repository_url" {
  description = "URL of the Backend ECR repository"
  value       = aws_ecr_repository.backend.repository_url
}


output "api_gateway_https_url" {
  description = "The free HTTPS URL provided by AWS API Gateway"
  value       = aws_apigatewayv2_stage.default_stage.invoke_url
}
