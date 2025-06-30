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
      const response = await axios.get(`${API_BASE_URL}/status/${scanId}${showDebug ? '?debug=true' : ''}`);
      setResult(response.data);
    } catch (error) {
      console.error('Status check failed:', error);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Cat Detection Service</h1>
        
        <div className="upload-section">
          <input
            type="file"
            accept="image/jpeg,image/png"
            onChange={handleFileSelect}
            disabled={loading}
          />
          <button 
            onClick={uploadImage} 
            disabled={!selectedFile || loading}
          >
            {loading ? 'Processing...' : 'Upload & Scan'}
          </button>
        </div>

        {scanId && (
          <div className="status-section">
            <h3>Scan ID: {scanId}</h3>
            <button onClick={checkStatus}>Check Status</button>
            <label>
              <input
                type="checkbox"
                checked={showDebug}
                onChange={(e) => setShowDebug(e.target.checked)}
              />
              Show Debug Data
            </label>
          </div>
        )}

        {result && (
          <div className="result-section">
            <h3>Result</h3>
            <p><strong>Status:</strong> {result.status}</p>
            {result.status === 'COMPLETED' && (
              <>
                <p className={`answer ${result.has_cat ? 'yes' : 'no'}`}>
                  <strong>Contains Cat:</strong> {result.answer}
                </p>
                <p><strong>Confidence:</strong> {result.confidence?.toFixed(2)}%</p>
                {showDebug && result.debug_labels && (
                  <div className="debug-section">
                    <h4>Debug Labels:</h4>
                    <ul>
                      {result.debug_labels.map((label, index) => (
                        <li key={index}>
                          {label.name}: {label.confidence.toFixed(2)}%
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
            {result.status === 'ERROR' && (
              <p className="error">Error: {result.error_message}</p>
            )}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;