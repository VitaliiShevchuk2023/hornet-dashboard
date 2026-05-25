variable "project_name" {
  description = "Project name — used as prefix for all Azure resources"
  type        = string
  default     = "hornet-dashboard"
}

variable "environment" {
  description = "Deployment environment: dev | staging | prod"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
  default     = "latest"
}

variable "eu_hornet_gdrive_id" {
  description = "Google Drive file ID for European hornet CSV"
  type        = string
  sensitive   = true
  default     = ""
}

variable "as_hornet_gdrive_id" {
  description = "Google Drive file ID for Asian hornet CSV"
  type        = string
  sensitive   = true
  default     = ""
}

variable "min_replicas" {
  description = "Minimum number of container replicas (0 = scale to zero)"
  type        = number
  default     = 0
}

variable "max_replicas" {
  description = "Maximum number of container replicas"
  type        = number
  default     = 3
}

variable "cpu" {
  description = "vCPU per replica"
  type        = string
  default     = "0.5"
}

variable "memory" {
  description = "Memory per replica"
  type        = string
  default     = "1Gi"
}
