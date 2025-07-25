# Silver Fox Scraper System - Deployment Guide

## 🚀 Complete Production Deployment Guide

This guide provides step-by-step instructions for deploying the Silver Fox Scraper System to production with comprehensive monitoring, alerting, and validation.

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Monitoring & Alerting Setup](#monitoring--alerting-setup)
5. [Scraper Validation](#scraper-validation)
6. [Production Testing](#production-testing)
7. [Maintenance & Operations](#maintenance--operations)
8. [Troubleshooting](#troubleshooting)

---

## 🔍 Pre-Deployment Checklist

### ✅ System Requirements

- **Kubernetes Cluster**: v1.20+ with at least 3 nodes
- **Node Resources**: 
  - Minimum: 4 CPU cores, 8GB RAM per node
  - Recommended: 8 CPU cores, 16GB RAM per node
- **Storage**: Persistent storage with at least 100GB available
- **Network**: Outbound HTTPS access for scraping
- **DNS**: Proper DNS configuration for ingress

### ✅ Required Services

- **Redis**: For caching and job queues
- **Prometheus**: For metrics collection
- **Grafana**: For dashboards and visualization
- **NGINX Ingress Controller**: For external access
- **cert-manager**: For TLS certificates (optional but recommended)

### ✅ Required Credentials

- **PipeDrive API Token**: For CRM integration
- **Email SMTP Credentials**: For alerts
- **Slack Webhook URL**: For notifications (optional)
- **Twilio Credentials**: For SMS alerts (optional)

---

## 🔧 Environment Setup

### 1. Create Namespace and Configure kubectl

```bash
# Create namespace
kubectl create namespace silverfox-scrapers

# Set as default namespace for convenience
kubectl config set-context --current --namespace=silverfox-scrapers
```

### 2. Configure Secrets

First, update the secrets in `kubernetes/secrets.yaml` with your actual credentials:

```bash
# Edit secrets file
vi kubernetes/secrets.yaml

# Update the following values (base64 encoded):
# - pipedrive_api_token
# - pipedrive_company_domain
# - smtp_username
# - smtp_password
# - redis_password
# - alert_email_recipients
```

### 3. Update Configuration

Edit `kubernetes/configmap.yaml` to match your environment:

```yaml
# Update dealership configurations
# Update scraping schedules
# Update monitoring thresholds
# Update alert rules
```

---

## ☸️ Kubernetes Deployment

### Deploy in Order

1. **Namespace and Basic Resources**:
```bash
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/rbac.yaml
kubectl apply -f kubernetes/storage.yaml
```

2. **Configuration and Secrets**:
```bash
kubectl apply -f kubernetes/secrets.yaml
kubectl apply -f kubernetes/configmap.yaml
```

3. **Redis Database**:
```bash
kubectl apply -f kubernetes/redis.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis --timeout=300s
```

4. **Core Application**:
```bash
kubectl apply -f kubernetes/scraper-deployment.yaml
kubectl apply -f kubernetes/services.yaml

# Wait for deployments to be ready
kubectl wait --for=condition=available deployment --all --timeout=600s
```

5. **Monitoring Stack**:
```bash
kubectl apply -f kubernetes/monitoring.yaml

# Wait for monitoring services
kubectl wait --for=condition=ready pod -l app=prometheus --timeout=300s
kubectl wait --for=condition=ready pod -l app=grafana --timeout=300s
```

6. **Auto-scaling and Jobs**:
```bash
kubectl apply -f kubernetes/hpa.yaml
kubectl apply -f kubernetes/cronjobs.yaml
```

7. **Ingress and Networking**:
```bash
# Update domain names in ingress.yaml first!
vi kubernetes/ingress.yaml

kubectl apply -f kubernetes/ingress.yaml
```

### Verify Deployment

```bash
# Check all pods are running
kubectl get pods

# Check services
kubectl get services

# Check ingress
kubectl get ingress

# Check logs
kubectl logs -l app=silverfox-scraper-system --tail=50
```

---

## 📊 Monitoring & Alerting Setup

### 1. Access Grafana Dashboard

```bash
# Get Grafana service URL
kubectl get service grafana-service

# For local access via port-forward:
kubectl port-forward service/grafana-service 3000:3000

# Access at: http://localhost:3000
# Default credentials: admin / silverfox123 (CHANGE IMMEDIATELY!)
```

### 2. Configure Prometheus Data Source

1. Login to Grafana
2. Go to Configuration → Data Sources
3. Add Prometheus data source:
   - URL: `http://prometheus-service:9090`
   - Access: Server (default)

### 3. Deploy Custom Dashboards

```bash
# Run the dashboard generator
cd core/monitoring
python grafana_dashboard_generator.py

# Or manually import the dashboard JSON files from the generator
```

### 4. Start Advanced Alerting System

```bash
# Deploy advanced alerting
kubectl create configmap alerting-config --from-file=core/monitoring/advanced_alerting_system.py

# Update deployment to include alerting component
kubectl patch deployment silverfox-analytics-processor -p '{"spec":{"template":{"spec":{"containers":[{"name":"alerting","image":"python:3.9","command":["python","/app/advanced_alerting_system.py"]}]}}}}'
```

### 5. Start Prometheus Exporter

```bash
# Deploy metrics exporter
kubectl create configmap metrics-exporter --from-file=core/monitoring/prometheus_exporter.py

# The exporter should auto-start with the main deployment
kubectl logs -l component=metrics-exporter
```

---

## 🧪 Scraper Validation

### 1. Run Comprehensive Stress Test

```bash
# First, run the stress test with mock data
cd tests
python stress_test_individual_scrapers.py

# Review results
cat stress_test_results/summary_*.json
```

### 2. Production Validation (Dry Run)

```bash
# Test scraper configuration without hitting live sites
python production_scraper_validator.py

# Review dry run results
cat production_validation_results/validation_summary_dry_run_*.json
```

### 3. Production Validation (Live Test)

⚠️ **CAUTION**: Only run this after confirming with the user and ensuring rate limiting is properly configured.

```bash
# Test against live websites (USE WITH CAUTION!)
python production_scraper_validator.py --live

# Test individual scraper
python production_scraper_validator.py --scraper jaguar_ranch_mirage --live

# Review live test results
cat production_validation_results/validation_summary_live_*.json
```

---

## 🧑‍💻 Production Testing

### 1. Manual Trigger Test

```bash
# Manually trigger a scraper job
kubectl create job --from=cronjob/silverfox-ranch-mirage-scraper manual-test-$(date +%s)

# Watch job progress
kubectl logs job/manual-test-xxxxx -f
```

### 2. End-to-End Integration Test

```bash
# Test full pipeline: scraping → processing → alerts → PipeDrive
kubectl exec -it deployment/silverfox-coordinator -- python -c "
import asyncio
from integration_test import run_e2e_test
asyncio.run(run_e2e_test())
"
```

### 3. Load Testing

```bash
# Run load test with multiple concurrent scrapers
kubectl scale deployment silverfox-scraper-workers --replicas=5

# Monitor resource usage
kubectl top pods
kubectl top nodes
```

### 4. Verify Data Flow

1. **Check Redis queues**:
```bash
kubectl exec -it deployment/redis -- redis-cli
> LLEN scraper_jobs
> LLEN analysis_jobs
```

2. **Check PipeDrive integration**:
```bash
# Review PipeDrive sync logs
kubectl logs -l component=pipedrive-sync --tail=100
```

3. **Check alert delivery**:
```bash
# Check alert system logs
kubectl logs -l component=alerting --tail=100
```

---

## 🔧 Maintenance & Operations

### Daily Operations

1. **Monitor System Health**:
```bash
# Check overall system status
kubectl get pods -o wide

# Check metrics in Grafana
# URL: https://grafana.silverfox-scrapers.yourdomain.com
```

2. **Review Scraper Performance**:
```bash
# Check recent scraper runs
kubectl get jobs --sort-by=.metadata.creationTimestamp

# Review any failed jobs
kubectl get jobs --field-selector=status.successful=0
```

3. **Monitor Resource Usage**:
```bash
# Check resource utilization
kubectl top pods
kubectl top nodes

# Check HPA status
kubectl get hpa
```

### Weekly Maintenance

1. **Update Scraper Configurations**:
```bash
# Update ConfigMap if needed
kubectl edit configmap silverfox-scraper-config

# Restart deployments to pick up changes
kubectl rollout restart deployment/silverfox-scraper-coordinator
kubectl rollout restart deployment/silverfox-scraper-workers
```

2. **Clean Up Old Jobs**:
```bash
# Clean up completed jobs older than 7 days
kubectl delete job $(kubectl get job -o jsonpath='{.items[?(@.status.completionTime<"'$(date -d '7 days ago' -Ins --utc | sed 's/+0000/Z/')'")].metadata.name}')
```

3. **Review and Rotate Logs**:
```bash
# Check log storage usage
kubectl exec -it deployment/silverfox-coordinator -- df -h /app/logs

# Archive old logs if needed
kubectl exec -it deployment/silverfox-coordinator -- find /app/logs -name "*.log" -mtime +30 -exec gzip {} \;
```

### Monthly Tasks

1. **Security Updates**:
```bash
# Update container images
kubectl set image deployment/silverfox-coordinator coordinator=silverfox/coordinator:latest
kubectl set image deployment/silverfox-workers worker=silverfox/worker:latest

# Verify rollout
kubectl rollout status deployment/silverfox-coordinator
kubectl rollout status deployment/silverfox-workers
```

2. **Performance Review**:
- Review Grafana dashboards for trends
- Analyze scraper success rates
- Review resource utilization patterns
- Update HPA settings if needed

3. **Backup Configuration**:
```bash
# Backup all configurations
kubectl get all,configmap,secret -o yaml > silverfox-backup-$(date +%Y%m%d).yaml
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Pods Stuck in Pending State

```bash
# Check node resources
kubectl describe nodes

# Check for resource constraints
kubectl describe pod <pod-name>

# Solution: Scale cluster or reduce resource requests
```

#### 2. Scraper Jobs Failing

```bash
# Check job logs
kubectl logs job/<job-name>

# Check for common issues:
# - Network connectivity
# - Website changes
# - Rate limiting
# - Chrome/ChromeDriver issues

# Restart job with debug logging
kubectl create job debug-job --from=cronjob/<cronjob-name>
kubectl logs job/debug-job -f
```

#### 3. High Error Rates

```bash
# Check alerting logs
kubectl logs -l component=alerting

# Review Prometheus metrics
kubectl port-forward service/prometheus-service 9090:9090
# Access: http://localhost:9090

# Common queries:
# - rate(silverfox_scraper_errors_total[5m])
# - silverfox_scraper_success_rate
```

#### 4. PipeDrive Integration Issues

```bash
# Check PipeDrive credentials
kubectl get secret silverfox-api-secrets -o yaml

# Test PipeDrive connectivity
kubectl exec -it deployment/silverfox-coordinator -- python -c "
import requests
response = requests.get('https://YOUR_DOMAIN.pipedrive.com/api/v1/users?api_token=YOUR_TOKEN')
print(response.status_code, response.text)
"
```

#### 5. Chrome Browser Issues

```bash
# Check Chrome processes
kubectl exec -it deployment/silverfox-workers -- ps aux | grep chrome

# Clean up zombie Chrome processes
kubectl exec -it deployment/silverfox-workers -- pkill -f chrome

# Restart worker pods
kubectl delete pods -l component=scraper-worker
```

### Emergency Procedures

#### System-Wide Failure

```bash
# 1. Scale down all components
kubectl scale deployment --all --replicas=0

# 2. Check cluster resources
kubectl get events --sort-by=.metadata.creationTimestamp

# 3. Restore from backup
kubectl apply -f silverfox-backup-YYYYMMDD.yaml

# 4. Scale back up gradually
kubectl scale deployment silverfox-coordinator --replicas=1
kubectl scale deployment silverfox-workers --replicas=2
```

#### Data Corruption

```bash
# 1. Stop all scrapers
kubectl patch cronjob --all -p '{"spec":{"suspend":true}}'

# 2. Backup current data
kubectl exec -it deployment/redis -- redis-cli BGSAVE

# 3. Clean corrupted data
kubectl exec -it deployment/redis -- redis-cli FLUSHDB

# 4. Restart from clean state
kubectl rollout restart deployment --all
```

---

## 📞 Support Contacts

- **Primary Developer**: Claude (Silver Fox Assistant)
- **Emergency Contact**: [Your contact information]
- **Documentation**: This deployment guide
- **Issue Tracking**: [Your issue tracking system]

---

## 📚 Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Redis Operations](https://redis.io/documentation)
- [PipeDrive API Documentation](https://developers.pipedrive.com/)

---

## 🔄 Version History

- **v1.0** (July 2025): Initial production deployment
- **v1.1**: Added advanced monitoring and alerting
- **v1.2**: Enhanced stress testing and validation

---

*This deployment guide is part of the Silver Fox Scraper System. For updates and support, consult the project documentation.*