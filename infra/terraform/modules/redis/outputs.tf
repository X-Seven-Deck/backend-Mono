output "redis_endpoint" {
  description = "The endpoint of the Redis cluster"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}

output "redis_port" {
  description = "The port of the Redis cluster"
  value       = aws_elasticache_replication_group.redis.port
}

output "redis_security_group_id" {
  description = "The ID of the security group created for the Redis cluster"
  value       = aws_security_group.redis.id
}

output "redis_replication_group_id" {
  description = "The ID of the Redis replication group"
  value       = aws_elasticache_replication_group.redis.id
}
