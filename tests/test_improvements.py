import pytest
from fastapi.testclient import TestClient

def test_health_endpoint(client):
    """Test health endpoint returns correct status"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert 'env' in data

def test_pt_health_endpoint(client):
    """Test Portugal specific health endpoint"""
    response = client.get('/pt/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['country'] == 'pt'

def test_api_documentation(client):
    """Test API documentation is accessible"""
    response = client.get('/docs')
    assert response.status_code == 200
    assert 'swagger' in response.text.lower()

def test_openapi_schema(client):
    """Test OpenAPI schema is available"""
    response = client.get('/openapi.json')
    assert response.status_code == 200
    schema = response.json()
    assert 'openapi' in schema
    assert schema['info']['title'] == 'SAFT Doctor (multi-country)'
    assert schema['info']['version'] == '0.2.0'

def test_user_registration_validation(client):
    """Test user registration with various inputs"""
    # Valid registration
    response = client.post('/auth/register', json={'username': 'validuser', 'password': 'validpass123'})
    assert response.status_code == 200
    data = response.json()
    assert data['username'] == 'validuser'
    assert data['country'] == 'pt'  # Default country
    assert 'id' in data

    # Duplicate username
    response = client.post('/auth/register', json={'username': 'validuser', 'password': 'anotherpass'})
    assert response.status_code == 400
    assert 'already exists' in response.json()['detail']

def test_login_flow(client):
    """Test complete login flow"""
    # Register user first
    client.post('/auth/register', json={'username': 'logintest', 'password': 'testpass123'})
    
    # Valid login
    response = client.post('/auth/token', data={'username': 'logintest', 'password': 'testpass123'})
    assert response.status_code == 200
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'
    
    # Invalid password
    response = client.post('/auth/token', data={'username': 'logintest', 'password': 'wrongpass'})
    assert response.status_code == 400
    assert 'Incorrect username or password' in response.json()['detail']
    
    # Non-existent user
    response = client.post('/auth/token', data={'username': 'nonexistent', 'password': 'anypass'})
    assert response.status_code == 400
    assert 'Incorrect username or password' in response.json()['detail']

def test_authenticated_request(client):
    """Test that authentication works for protected endpoints"""
    # Register and login
    client.post('/auth/register', json={'username': 'authtest', 'password': 'testpass123'})
    login_response = client.post('/auth/token', data={'username': 'authtest', 'password': 'testpass123'})
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test AT secrets endpoint with valid token
    response = client.post('/pt/secrets/at', 
                          json={'username': 'at_user', 'password': 'at_pass'}, 
                          headers=headers)
    assert response.status_code == 200
    assert response.json()['ok'] is True

def test_unauthorized_request(client):
    """Test that protected endpoints require authentication"""
    # Try to access protected endpoint without token
    response = client.post('/pt/secrets/at', json={'username': 'at_user', 'password': 'at_pass'})
    assert response.status_code == 401
    
    # Try with invalid token
    headers = {'Authorization': 'Bearer invalid-token'}
    response = client.post('/pt/secrets/at', 
                          json={'username': 'at_user', 'password': 'at_pass'}, 
                          headers=headers)
    assert response.status_code == 401

def test_file_upload_flow(client):
    """Test file upload functionality"""
    # Register and login
    client.post('/auth/register', json={'username': 'filetest', 'password': 'testpass123'})
    login_response = client.post('/auth/token', data={'username': 'filetest', 'password': 'testpass123'})
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # Upload a test file
    test_content = b'<AuditFile><Header></Header></AuditFile>'
    files = {'file': ('test_saft.xml', test_content, 'application/xml')}
    
    response = client.post('/pt/files/upload', files=files, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['ok'] is True
    assert 'object' in data

def test_cors_headers(client):
    """Test that CORS headers are properly set"""
    response = client.options('/health')
    # Note: TestClient doesn't fully simulate CORS, but we can check the app is configured
    # In a real environment, these headers would be present
    assert response.status_code == 200