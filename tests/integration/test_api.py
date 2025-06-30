import pytest
import requests
import base64
import json
import time
import os
from PIL import Image
import io

API_URL = os.environ.get('API_URL', 'https://api.example.com/dev')

class TestCatDetectionAPI:
    
    def setup_method(self):
        """Setup test data"""
        # Create a simple test image
        self.test_image = self._create_test_image()
        self.cat_image_b64 = base64.b64encode(self.test_image).decode('utf-8')
    
    def _create_test_image(self):
        """Create a simple PNG image for testing"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    def test_upload_valid_image(self):
        """Test uploading a valid PNG image"""
        response = requests.post(f"{API_URL}/upload", json={
            'image_data': self.cat_image_b64,
            'content_type': 'image/png',
            'user_id': 'test-user'
        })
        
        assert response.status_code == 200
        data = response.json()
        assert 'scan_id' in data
        assert data['status'] == 'PENDING'
        
        return data['scan_id']
    
    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        response = requests.post(f"{API_URL}/upload", json={
            'image_data': self.cat_image_b64,
            'content_type': 'image/gif',  # Invalid
            'user_id': 'test-user'
        })
        
        assert response.status_code == 400
        data = response.json()
        assert 'error' in data
    
    def test_check_status_nonexistent(self):
        """Test checking status of non-existent scan"""
        fake_id = 'non-existent-id'
        response = requests.get(f"{API_URL}/status/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert 'error' in data
    
    def test_full_workflow(self):
        """Test complete upload -> process -> check status workflow"""
        # Upload image
        scan_id = self.test_upload_valid_image()
        
        # Poll for completion (max 60 seconds)
        start_time = time.time()
        max_wait = 60
        
        while time.time() - start_time < max_wait:
            response = requests.get(f"{API_URL}/status/{scan_id}")
            assert response.status_code == 200
            
            data = response.json()
            if data['status'] == 'COMPLETED':
                assert 'has_cat' in data
                assert 'answer' in data
                assert data['answer'] in ['Yes', 'No']
                break
            elif data['status'] == 'ERROR':
                pytest.fail(f"Processing failed: {data.get('error_message', 'Unknown error')}")
            
            time.sleep(2)
        else:
            pytest.fail("Processing did not complete within timeout")
    
    def test_debug_mode(self):
        """Test debug mode returns additional data"""
        scan_id = self.test_upload_valid_image()
        
        # Wait for processing
        time.sleep(10)
        
        response = requests.get(f"{API_URL}/status/{scan_id}?debug=true")
        assert response.status_code == 200
        
        data = response.json()
        if data['status'] == 'COMPLETED':
            assert 'debug_labels' in data
