# 🐱 Cat Detection Service

A serverless image processing service that detects cats in uploaded images using AWS Rekognition, built for the **ICE Senior Platform Engineer** role.

![Architecture Diagram](https://img.shields.io/badge/AWS-Serverless-orange) ![CI/CD](https://img.shields.io/badge/CI/CD-GitHub%20Actions-blue) ![Infrastructure](https://img.shields.io/badge/Infrastructure-Terraform-purple)

## 📋 Overview

This project implements a cloud-native, serverless cat detection service that allows users to upload images and receive analysis results indicating whether cats are present. The solution demonstrates modern DevOps practices, infrastructure as code, and AWS serverless architecture.

### 🎯 Requirements Implemented

- ✅ **Image Upload**: Support for JPEG/PNG files via REST API and web interface
- ✅ **Persistent Storage**: Images and results stored reliably in AWS S3 and DynamoDB
- ✅ **Asynchronous Processing**: Non-blocking image analysis using SQS queues
- ✅ **REST API**: Well-defined endpoints for upload and status checking
- ✅ **Web Interface**: React-based UI for easy interaction
- ✅ **Debug Information**: Detailed analysis data for power users
- ✅ **Multi-Environment**: Dev, staging, and production deployments
- ✅ **Infrastructure as Code**: Complete Terraform configuration
- ✅ **CI/CD Pipeline**: Automated deployment via GitHub Actions

## 🏗️ Architecture

### High-Level Architecture
```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   React UI  │───▶│ API Gateway  │───▶│   Lambda    │───▶│  S3 Bucket   │
│ (CloudFront)│    │              │    │  (Upload)   │    │  (Images)    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                           │                    │
                           │                    ▼
                           │            ┌─────────────┐
                           │            │ SQS Queue   │
                           │            │ (Processing)│
                           │            └─────────────┘
                           │                    │
                           │                    ▼
                           │            ┌─────────────┐    ┌──────────────┐
                           │            │   Lambda    │───▶│  DynamoDB    │
                           │            │ (Process)   │    │ (Results)    │
                           │            └─────────────┘    └──────────────┘
                           │                    │
                           │                    ▼
                           │            ┌─────────────┐
                           ▼            │   AWS       │
                   ┌─────────────┐     │ Rekognition │
                   │   Lambda    │◀────│ (ML Service)│
                   │  (Status)   │     └─────────────┘
                   └─────────────┘
```

### AWS Services Used
- **API Gateway**: REST API endpoints
- **Lambda**: Serverless compute (upload, process, status)
- **S3**: Object storage for images and web UI hosting
- **DynamoDB**: NoSQL database for scan results
- **SQS**: Message queuing for asynchronous processing
- **Rekognition**: Machine learning for image analysis
- **CloudFront**: CDN for web UI distribution
- **CloudWatch**: Monitoring, logging, and alerting

## 🚀 Live Demo

### Try It Now!
**🌐 Web Interface**: https://d1frt8mu4yn6nr.cloudfront.net

### How to Use:
1. **Visit the web interface** → https://d1frt8mu4yn6nr.cloudfront.net
2. **Select an image** → Choose any JPEG or PNG file containing cats (or not!)
3. **Upload & Scan** → Click the upload button and wait for processing
4. **View Results** → See if cats were detected with confidence scores
5. **Enable Debug Mode** → Toggle "Show Debug Data" for detailed analysis

### API Endpoints (For Developers)
**Base URL**: https://ci1eovz6lk.execute-api.eu-west-1.amazonaws.com/dev

```bash
# Upload an image (Base64 JSON format)
POST /upload
Content-Type: application/json
{
  "image_data": "base64-encoded-image-data",
  "content_type": "image/jpeg",
  "user_id": "your-user-id"
}

# Check scan status
GET /status/{scan_id}?debug=true  # Optional debug parameter
```

### Example API Usage (Advanced Users)
```python
import requests
import base64

# Encode your image
with open('cat.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Upload image
response = requests.post(
    'https://ci1eovz6lk.execute-api.eu-west-1.amazonaws.com/dev/upload',
    json={
        "image_data": image_data,
        "content_type": "image/jpeg", 
        "user_id": "demo-user"
    }
)

scan_id = response.json()['scan_id']

# Check results with debug data
status = requests.get(
    f'https://ci1eovz6lk.execute-api.eu-west-1.amazonaws.com/dev/status/{scan_id}?debug=true'
)
print(status.json())
```

## 🛠️ Technology Stack

### Backend
- **Runtime**: Python 3.11
- **Framework**: AWS Lambda
- **Database**: DynamoDB (on-demand)
- **Storage**: S3
- **Queue**: SQS with DLQ
- **ML Service**: AWS Rekognition

### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS
- **Build**: Create React App
- **Hosting**: S3 + CloudFront

### Infrastructure
- **IaC**: Terraform
- **CI/CD**: GitHub Actions
- **Environments**: Dev, Staging, Production
- **Monitoring**: CloudWatch

### Development Tools
- **Version Control**: Git + GitHub
- **Testing**: pytest, integration tests
- **Security**: Bandit, Safety, TFSec
- **Linting**: Standard Python/JS tools

## 📁 Project Structure

```
cat-detection-service/
├── .github/workflows/          # CI/CD pipelines
│   ├── deploy-dev.yml         # Development deployment
│   ├── deploy-staging.yml     # Staging deployment
│   ├── deploy-prod.yml        # Production deployment
│   └── destroy-infrastructure.yml # Infrastructure cleanup
├── terraform/                 # Infrastructure as Code
│   ├── environments/          # Environment-specific configs
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── modules/               # Reusable Terraform modules
│       ├── api-gateway/
│       ├── lambda/
│       ├── storage/
│       ├── web-ui/
│       └── monitoring/
├── src/
│   ├── lambdas/               # Lambda function code
│   │   ├── upload/            # Image upload handler
│   │   ├── process/           # Image processing handler
│   │   └── status/            # Status check handler
│   └── web-ui/                # React frontend
│       ├── public/
│       ├── src/
│       └── package.json
├── tests/                     # Test suites
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── requirements.txt       # Test dependencies
├── scripts/                   # Utility scripts
│   ├── bootstrap-terraform.sh # Backend setup
│   └── destroy-environment.sh # Environment cleanup
├── README.md                  # This file
├── .gitignore                # Git ignore rules
└── requirements.txt          # Python dependencies
```

## 🚦 Getting Started

### Prerequisites
- AWS CLI configured with appropriate permissions
- Terraform >= 1.5.0
- Node.js >= 18
- Python >= 3.11
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cat-detection-service
   ```

2. **Bootstrap Terraform backend**
   ```bash
   ./scripts/bootstrap-terraform.sh dev
   ```

3. **Deploy infrastructure**
   ```bash
   cd terraform/environments/dev
   terraform init
   terraform apply
   ```

4. **Deploy web UI**
   ```bash
   cd ../../../src/web-ui
   npm install
   npm run build
   # Deploy to S3 (automated in CI/CD)
   ```

### Environment Deployment

The project uses GitOps workflow:

```bash
# Deploy to dev (automatic on push to develop)
git push origin develop

# Deploy to staging (automatic on push to main)
git checkout main
git merge develop
git push origin main

# Deploy to production (on release creation)
git tag v1.0.0
git push origin v1.0.0
```

## 🧪 Testing

### Run Unit Tests
```bash
cd tests
pip install -r requirements.txt
pytest unit/ -v
```

### Run Integration Tests
```bash
export API_BASE_URL=https://your-api-gateway-url.amazonaws.com/dev
pytest integration/ -v
```

### Manual Testing
```bash
# Test upload endpoint
curl -X POST \
  $API_BASE_URL/upload \
  -F 'image=@test-cat.jpg'

# Test status endpoint
curl $API_BASE_URL/status/scan-id-here?debug=true
```

## 📊 Monitoring & Observability

### CloudWatch Dashboards
- API Gateway metrics (requests, latency, errors)
- Lambda metrics (duration, errors, concurrent executions)
- DynamoDB metrics (read/write capacity, throttling)
- SQS metrics (messages sent, received, DLQ)

### Alarms Configured
- Lambda function errors > 1%
- API Gateway 5xx errors > 5%
- Lambda duration > 10 seconds
- SQS DLQ messages > 0

### Log Aggregation
- All Lambda functions log to CloudWatch
- API Gateway access logs enabled
- Structured logging with correlation IDs

## 🔒 Security

### Security Measures Implemented
- **IAM**: Least privilege access for all resources
- **API Gateway**: Request throttling and validation
- **S3**: Bucket policies and public access blocks
- **Lambda**: Runtime security scanning
- **Dependencies**: Vulnerability scanning with Safety
- **Infrastructure**: Security scanning with TFSec

### Security Scans
- **Bandit**: Python code security analysis
- **Safety**: Dependency vulnerability scanning
- **TFSec**: Terraform security best practices

## 💰 Cost Optimization

### Current Cost Estimate (Development)
- **Monthly**: ~£4-8 for light usage
- **Pay-per-use**: Costs scale with actual usage
- **Free tier**: Leverages AWS free tier where possible

### Cost Breakdown (GBP)
- Lambda: £0.40/month (estimated)
- API Gateway: £0.08/month
- S3: £0.80/month (storage + requests)
- DynamoDB: £0.20/month (on-demand)
- CloudWatch: £1.60/month (logs + metrics)
- Other services: £1.72/month

*Costs calculated at current GBP/USD exchange rates and may vary based on actual usage patterns.*

## 🚀 Production Readiness

### Implemented Features
- ✅ Multi-environment deployment
- ✅ Infrastructure as Code
- ✅ Automated CI/CD pipeline
- ✅ Comprehensive monitoring
- ✅ Error handling and retries
- ✅ Security best practices
- ✅ Cost optimization
- ✅ Documentation

### Production Considerations
- **Scaling**: Auto-scaling with Lambda concurrency controls
- **Backup**: DynamoDB point-in-time recovery available
- **Disaster Recovery**: Multi-AZ deployment by default
- **Performance**: CloudFront global edge caching
- **Security**: WAF and enhanced monitoring for production

## 📈 Performance

### Expected Performance
- **API Latency**: < 200ms (95th percentile)
- **Image Processing**: 2-5 seconds per image
- **Throughput**: 1000+ concurrent requests
- **Availability**: 99.9% (AWS SLA)

### Optimization Features
- **Async Processing**: Non-blocking upload/process flow
- **CDN**: Global content delivery via CloudFront
- **Caching**: API Gateway response caching available
- **Connection Pooling**: Optimized Lambda runtime

## 🛠️ Development Workflow

### Branching Strategy
- `develop`: Development branch (deploys to dev)
- `main`: Staging branch (deploys to staging)
- `tags/releases`: Production deployment

### GitOps Deployment Flow
```bash
# Deploy to dev (automatic on push to develop)
git push origin develop

# Deploy to staging (automatic on push to main)
git checkout main
git merge develop
git push origin main

# Deploy to production (on release creation)
git tag v1.0.0
git push origin v1.0.0
```

### Infrastructure Management
```bash
# Create new environments
./scripts/bootstrap-terraform.sh [dev|staging|prod]

# Destroy environments (via GitHub Actions)
# Go to: Actions → Destroy Infrastructure → Run workflow
# Select environment and type "DESTROY" to confirm
```

### Code Quality
- Python: PEP 8 compliance
- JavaScript: ESLint configuration
- Security: Automated scanning in CI/CD
- Testing: Unit and integration test coverage

## 📞 Support & Troubleshooting

### Common Issues
1. **Upload fails**: Check file format (JPEG/PNG only)
2. **Slow processing**: Normal for Rekognition analysis (2-5s)
3. **403 errors**: Verify CORS configuration

### Monitoring
- Check CloudWatch logs for detailed error information
- Use scan_id for tracing requests end-to-end
- Monitor DLQ for failed processing attempts

### Debug Mode
Add `?debug=true` to status endpoint for detailed information:
```bash
curl $API_BASE_URL/status/scan-id?debug=true
```

## 🤝 Contributing

This project was developed for the ICE Senior Platform Engineer interview process. The implementation demonstrates:

- **Cloud Architecture**: Serverless, scalable, cost-effective
- **DevOps Practices**: IaC, CI/CD, monitoring, security
- **Software Engineering**: Clean code, testing, documentation
- **AWS Expertise**: Service integration, best practices

## 📄 License

This project is for interview/evaluation purposes.

---

**Built with ❤️ for ICE International Copyright Enterprise**

*Demonstrating modern cloud architecture and DevOps excellence*