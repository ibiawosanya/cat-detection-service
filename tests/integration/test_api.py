import pytest
import requests
import base64
import time
import os
from io import BytesIO
from PIL import Image

# API Configuration - will be set by environment variable in CI/CD
API_BASE_URL = os.getenv('API_BASE_URL', 'https://gculxuhkz2.execute-api.eu-west-1.amazonaws.com/dev')


@pytest.fixture
def sample_image_base64():
    """Create a small test image and convert to base64"""
    # Create a small 10x10 red image for testing
    img = Image.new('RGB', (10, 10), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_data = buffer.getvalue()
    return base64.b64encode(img_data).decode('utf-8')


class TestCatDetectionAPI:
    """Integration tests for the Cat Detection API"""
    
    def test_upload_valid_image(self, sample_image_base64):
        """Test uploading a valid image to the API"""
        upload_data = {
            'image_data': sample_image_base64,
            'content_type': 'image/jpeg',
            'user_id': 'test-user'
        }
        
        response = requests.post(f'{API_BASE_URL}/upload', json=upload_data)
        
        assert response.status_code == 200
        data = response.json()
        assert 'scan_id' in data
        assert 'status' in data
        assert data['status'] == 'PENDING'
        # Don't return anything - just assert
    
    def test_upload_invalid_content_type(self, sample_image_base64):
        """Test uploading with invalid content type"""
        upload_data = {
            'image_data': sample_image_base64,
            'content_type': 'image/gif',  # Not allowed
            'user_id': 'test-user'
        }
        
        response = requests.post(f'{API_BASE_URL}/upload', json=upload_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'JPEG and PNG' in data['error']
    
    def test_upload_missing_data(self):
        """Test uploading without required image data"""
        upload_data = {
            'content_type': 'image/jpeg',
            'user_id': 'test-user'
            # Missing image_data
        }
        
        response = requests.post(f'{API_BASE_URL}/upload', json=upload_data)
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
        assert 'image_data' in data['error']
    
    def test_status_nonexistent_scan(self):
        """Test checking status of non-existent scan"""
        fake_scan_id = 'nonexistent-scan-id'
        
        response = requests.get(f'{API_BASE_URL}/status/{fake_scan_id}')
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_status_with_debug(self, sample_image_base64):
        """Test status endpoint with debug parameter"""
        # First upload an image
        upload_data = {
            'image_data': sample_image_base64,
            'content_type': 'image/jpeg',
            'user_id': 'test-user'
        }
        
        upload_response = requests.post(f'{API_BASE_URL}/upload', json=upload_data)
        assert upload_response.status_code == 200
        scan_id = upload_response.json()['scan_id']
        
        # Check status with debug
        response = requests.get(f'{API_BASE_URL}/status/{scan_id}?debug=true')
        
        assert response.status_code == 200
        data = response.json()
        assert 'scan_id' in data
        assert 'status' in data
        # Status should be PENDING, PROCESSING, or COMPLETED
        assert data['status'] in ['PENDING', 'PROCESSING', 'COMPLETED']
    
    @pytest.mark.slow
    def test_full_workflow(self, sample_image_base64):
        """Test the complete upload -> process -> result workflow"""
        # Upload image
        upload_data = {
            'image_data': sample_image_base64,
            'content_type': 'image/jpeg',
            'user_id': 'integration-test'
        }
        
        upload_response = requests.post(f'{API_BASE_URL}/upload', json=upload_data)
        assert upload_response.status_code == 200
        scan_id = upload_response.json()['scan_id']
        
        # Poll for completion (with timeout)
        max_attempts = 20  # 60 seconds max
        for attempt in range(max_attempts):
            response = requests.get(f'{API_BASE_URL}/status/{scan_id}')
            assert response.status_code == 200
            
            data = response.json()
            status = data['status']
            
            if status == 'COMPLETED':
                # Verify the response structure
                assert 'cats_found' in data
                assert 'cat_count' in data
                assert 'highest_confidence' in data
                assert isinstance(data['cats_found'], bool)
                assert isinstance(data['cat_count'], int)
                assert isinstance(data['highest_confidence'], (int, float))
                return  # Test passed
            
            elif status == 'ERROR':
                pytest.fail(f"Processing failed with error: {data.get('error_message', 'Unknown error')}")
            
            # Wait before next check
            time.sleep(3)
        
        pytest.fail(f"Processing did not complete within {max_attempts * 3} seconds")


class TestAPIHealth:
    """Basic health checks for the API"""
    
    def test_api_reachable(self):
        """Test that the API is reachable"""
        try:
            # Try to hit a known endpoint (even if it fails, we just want to reach the API)
            response = requests.get(f'{API_BASE_URL}/status/health-check')
            # We expect 404 (endpoint doesn't exist) but that means API is reachable
            assert response.status_code in [404, 400, 500]  # Any response means API is up
        except requests.exceptions.ConnectionError:
            pytest.fail("Cannot connect to API - check if service is deployed")
    
    def test_cors_headers(self, sample_image_base64):
        """Test that CORS headers are present"""
        upload_data = {
            'image_data': sample_image_base64,
            'content_type': 'image/jpeg'
        }
        
        response = requests.post(f'{API_BASE_URL}/upload', json=upload_data)
        
        # Check for CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers
        assert response.headers['Access-Control-Allow-Origin'] == '*'