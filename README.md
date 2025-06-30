# Cat Detector - AI-Powered Image Analysis Platform

## � ICE Senior Platform Engineer - Technical Demonstration

Enterprise-grade serverless application built with Pulumi for automated cat detection using AWS AI services.

### � Live Demo
- **Website:** https://d15numid98sk9j.cloudfront.net
- **API:** https://bd2r2ubz3g.execute-api.eu-west-1.amazonaws.com/dev

### �️ Architecture
- **Serverless:** AWS Lambda, API Gateway, S3, DynamoDB
- **AI/ML:** AWS Rekognition for image analysis
- **CDN:** CloudFront for global distribution
- **IaC:** Pulumi with multi-environment support
- **CI/CD:** GitHub Actions with automated testing

### � ICE Business Value
- **Content Processing:** Scalable AI pipeline for copyright analysis
- **Global Distribution:** GDPR-compliant EU deployment
- **Cost Optimization:** Pay-per-use serverless model
- **Platform Engineering:** Infrastructure as enablement tool

### � Quick Start
\`\`\`bash
# Deploy infrastructure
./scripts/deploy-pulumi.sh

# Run tests
./scripts/test-pulumi.sh

# Access application
open https://d15numid98sk9j.cloudfront.net
\`\`\`

### � Testing
\`\`\`bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/ -v

# Run specific test types
pytest tests/test_infrastructure.py -v  # Infrastructure tests
pytest tests/test_integration.py -v     # Integration tests
\`\`\`

### � CI/CD Pipeline
- **Code Quality:** Black, isort, flake8, bandit
- **Testing:** pytest with coverage reporting
- **Multi-Environment:** dev → staging → prod
- **Security:** Automated vulnerability scanning
- **Monitoring:** CloudWatch integration

### � Platform Engineering Features
- Infrastructure as Code with Pulumi
- Multi-cloud foundation (AWS + future expansion)
- Policy as Code with automated compliance
- Team self-service infrastructure
- Environment-specific configurations
- Comprehensive monitoring and alerting

### � Senior Platform Engineer Showcase
This implementation demonstrates:
- **Strategic Technology Choices:** Pulumi over CDK for multi-cloud flexibility
- **Platform Engineering Mindset:** Infrastructure as product for teams
- **Enterprise Readiness:** Security, monitoring, disaster recovery
- **Business Alignment:** Direct relevance to ICE's content processing needs
- **Operational Excellence:** Complete CI/CD with automated testing

---
**Built for ICE International Copyright Enterprise**  
Demonstrating platform engineering excellence and strategic technology leadership.
