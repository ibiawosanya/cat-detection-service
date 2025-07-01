import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_API_URL;

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [scanId, setScanId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDebug, setShowDebug] = useState(false);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && (file.type === 'image/jpeg' || file.type === 'image/png')) {
      setSelectedFile(file);
    } else {
      alert('Please select a JPEG or PNG file');
    }
  };

  const uploadImage = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setResult(null); // Clear previous results
    try {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = e.target.result.split(',')[1];
        
        const response = await axios.post(`${API_BASE_URL}/upload`, {
          image_data: base64Data,
          content_type: selectedFile.type,
          user_id: 'demo-user'
        });

        setScanId(response.data.scan_id);
        pollForResult(response.data.scan_id);
      };
      reader.readAsDataURL(selectedFile);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed');
      setLoading(false);
    }
  };

  const pollForResult = async (id) => {
    try {
      // Always use current showDebug state for polling
      const response = await axios.get(`${API_BASE_URL}/status/${id}${showDebug ? '?debug=true' : ''}`);
      
      if (response.data.status === 'COMPLETED') {
        setResult(response.data);
        setLoading(false);
      } else if (response.data.status === 'ERROR') {
        setResult(response.data);
        setLoading(false);
      } else {
        // Still pending, poll again in 2 seconds
        setTimeout(() => pollForResult(id), 2000);
      }
    } catch (error) {
      console.error('Status check failed:', error);
      setLoading(false);
    }
  };

  const checkStatus = async () => {
    if (!scanId) return;
    
    try {
      // Use current showDebug state
      const response = await axios.get(`${API_BASE_URL}/status/${scanId}${showDebug ? '?debug=true' : ''}`);
      setResult(response.data);
    } catch (error) {
      console.error('Status check failed:', error);
    }
  };

  // New function to handle debug toggle change
  const handleDebugToggle = (e) => {
    const newDebugState = e.target.checked;
    setShowDebug(newDebugState);
    
    // If we have a scan ID and want to refresh with new debug setting
    if (scanId && result) {
      checkStatus(); // This will use the new debug state
    }
  };

  // Function to get debug labels from the result
  const getDebugLabels = (result) => {
    // Try different possible locations for debug data
    if (result.debug_data && result.debug_data.all_labels) {
      return result.debug_data.all_labels;
    }
    if (result.debug_labels) {
      return result.debug_labels;
    }
    return null;
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🐱 Cat Detection Service</h1>
        <p>Upload an image to detect if it contains cats!</p>
        
        <div className="upload-section">
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={handleFileSelect}
            disabled={loading}
            style={{ marginBottom: '10px' }}
          />
          <br />
          <button 
            onClick={uploadImage} 
            disabled={!selectedFile || loading}
            style={{ 
              padding: '10px 20px', 
              fontSize: '16px',
              backgroundColor: loading ? '#ccc' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Processing...' : 'Upload & Scan for Cats'}
          </button>
        </div>

        {scanId && (
          <div className="status-section" style={{ margin: '20px 0' }}>
            <h3>Scan ID: {scanId}</h3>
            <button 
              onClick={checkStatus}
              style={{
                padding: '8px 16px',
                marginRight: '10px',
                backgroundColor: '#2196F3',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
            >
              Refresh Status
            </button>
            <label style={{ display: 'flex', alignItems: 'center', marginTop: '10px' }}>
              <input
                type="checkbox"
                checked={showDebug}
                onChange={handleDebugToggle}
                style={{ marginRight: '8px' }}
              />
              <strong>Show Debug Data (Power User Mode)</strong>
            </label>
            {showDebug && (
              <p style={{ fontSize: '12px', color: '#888', marginTop: '5px' }}>
                Debug mode will show detailed Rekognition analysis including all detected labels with confidence scores.
              </p>
            )}
          </div>
        )}

        {result && (
          <div className="result-section" style={{ 
            margin: '20px 0', 
            padding: '20px', 
            border: '2px solid #ddd', 
            borderRadius: '10px',
            backgroundColor: '#f9f9f9',
            color: '#333'
          }}>
            <h3>🔍 Analysis Results</h3>
            <p><strong>Status:</strong> {result.status}</p>
            
            {result.status === 'COMPLETED' && (
              <>
                <div style={{ 
                  padding: '15px', 
                  margin: '10px 0',
                  borderRadius: '8px',
                  backgroundColor: result.has_cat ? '#d4edda' : '#f8d7da',
                  border: `2px solid ${result.has_cat ? '#c3e6cb' : '#f5c6cb'}`,
                  fontSize: '18px'
                }}>
                  <strong>🐱 Contains Cat:</strong> 
                  <span style={{ 
                    fontSize: '24px', 
                    fontWeight: 'bold',
                    color: result.has_cat ? '#155724' : '#721c24'
                  }}>
                    {result.answer || (result.has_cat ? 'Yes' : 'No')}
                  </span>
                </div>
                
                <p><strong>🎯 Confidence:</strong> {result.confidence?.toFixed(2)}%</p>
                
                {result.cat_count > 0 && (
                  <p><strong>📊 Cat Labels Found:</strong> {result.cat_count}</p>
                )}
                
                <p><strong>📋 Total Labels Detected:</strong> {result.total_labels}</p>
                
                {showDebug && getDebugLabels(result) && (
                  <div className="debug-section" style={{ 
                    marginTop: '20px',
                    padding: '15px',
                    backgroundColor: '#e7f3ff',
                    border: '2px solid #0066cc',
                    borderRadius: '8px'
                  }}>
                    <h4 style={{ color: '#0066cc', marginBottom: '15px' }}>
                      🔧 Debug Data - All Detected Labels:
                    </h4>
                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                      {getDebugLabels(result).map((label, index) => (
                        <div key={index} style={{ 
                          marginBottom: '10px',
                          padding: '8px',
                          backgroundColor: 'white',
                          borderRadius: '4px',
                          border: '1px solid #ddd'
                        }}>
                          <strong>{label.Name || label.name}</strong>: {(label.Confidence || label.confidence)?.toFixed(2)}%
                          {label.Categories && label.Categories.length > 0 && (
                            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                              Categories: {label.Categories.join(', ')}
                            </div>
                          )}
                          {label.Instances && label.Instances.length > 0 && (
                            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                              Instances: {label.Instances.length} detected
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop: '10px', fontSize: '12px', color: '#666' }}>
                      <strong>Note:</strong> This debug information shows all labels detected by AWS Rekognition 
                      with confidence scores above 70%. Cat-related labels are used to determine the final result.
                    </div>
                  </div>
                )}
              </>
            )}
            
            {result.status === 'PROCESSING' && (
              <p style={{ color: '#ff9800' }}>⏳ Still processing your image...</p>
            )}
            
            {result.status === 'ERROR' && (
              <p className="error" style={{ color: '#f44336' }}>
                ❌ Error: {result.error_message}
              </p>
            )}
          </div>
        )}

        {!result && !loading && (
          <div style={{ marginTop: '20px', color: '#666' }}>
            <p>Select a JPEG or PNG image file and click "Upload & Scan for Cats" to get started!</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App;