output "rds_endpoint" {
  description = "The endpoint of the RDS instance"
  value       = aws_db_instance.rds.endpoint
}

output "rds_address" {
  description = "The address of the RDS instance"
  value       = aws_db_instance.rds.address
}

output "rds_port" {
  description = "The port of the RDS instance"
  value       = aws_db_instance.rds.port
}

output "rds_name" {
  description = "The name of the RDS instance"
  value       = aws_db_instance.rds.db_name
}

output "rds_username" {
  description = "The username of the RDS instance"
  value       = aws_db_instance.rds.username
  sensitive   = true
}

output "rds_security_group_id" {
  description = "The ID of the security group created for the RDS instance"
  value       = aws_security_group.rds.id
}
