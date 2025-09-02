import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import tempfile
import os
from io import BytesIO

# Import the FastAPI app from local_main.py
from local_main import app

client = TestClient(app)

@pytest.fixture
def mock_file():
    """Create a mock file for testing"""
    content = b"test file content"
    return ("test.pdf", BytesIO(content), "application/pdf")

@pytest.fixture
def mock_image_file():
    """Create a mock image file for testing"""
    content = b"fake image content"
    return ("test.jpg", BytesIO(content), "image/jpeg")

@pytest.fixture
def valid_form_data():
    """Valid form data for submit-details endpoint"""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "1234567890",
        "address": "123 Main St",
        "constituency": "Test Constituency"
    }

class TestVerifyDocumentEndpoint:
    """Test cases for /verify-document/ endpoint"""
    
    def test_verify_document_success(self, mock_file):
        """Test successful document verification"""
        filename, file_content, content_type = mock_file
        
        with patch('local_main.save_uploaded_file') as mock_save, \
             patch('local_main.process_document') as mock_process:
            
            mock_save.return_value = "/tmp/test.pdf"
            mock_process.return_value = {
                "status": "success",
                "document_type": "identity_card",
                "extracted_data": {"name": "John Doe", "id": "123456"}
            }
            
            response = client.post(
                "/verify-document/",
                files={"file": (filename, file_content, content_type)}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["document_type"] == "identity_card"
            assert "extracted_data" in data
    
    def test_verify_document_no_file(self):
        """Test document verification without file"""
        response = client.post("/verify-document/")
        
        assert response.status_code == 422
    
    def test_verify_document_invalid_file_type(self):
        """Test document verification with invalid file type"""
        invalid_file = ("test.txt", BytesIO(b"text content"), "text/plain")
        filename, file_content, content_type = invalid_file
        
        response = client.post(
            "/verify-document/",
            files={"file": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file type" in data["detail"]
    
    def test_verify_document_large_file(self):
        """Test document verification with file too large"""
        # Create a mock large file (> 10MB)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = ("large.pdf", BytesIO(large_content), "application/pdf")
        filename, file_content, content_type = large_file
        
        response = client.post(
            "/verify-document/",
            files={"file": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["detail"]
    
    @patch('local_main.save_uploaded_file')
    @patch('local_main.process_document')
    def test_verify_document_processing_error(self, mock_process, mock_save, mock_file):
        """Test document verification with processing error"""
        filename, file_content, content_type = mock_file
        
        mock_save.return_value = "/tmp/test.pdf"
        mock_process.side_effect = Exception("Processing failed")
        
        response = client.post(
            "/verify-document/",
            files={"file": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Error processing document" in data["detail"]
    
    @patch('local_main.save_uploaded_file')
    def test_verify_document_save_error(self, mock_save, mock_file):
        """Test document verification with file save error"""
        filename, file_content, content_type = mock_file
        
        mock_save.side_effect = Exception("Save failed")
        
        response = client.post(
            "/verify-document/",
            files={"file": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Error processing document" in data["detail"]

class TestSubmitDetailsEndpoint:
    """Test cases for /submit-details/ endpoint"""
    
    @patch('local_main.save_uploaded_file')
    @patch('local_main.save_to_database')
    def test_submit_details_success_with_files(self, mock_db_save, mock_file_save, 
                                             valid_form_data, mock_image_file):
        """Test successful details submission with files"""
        filename, file_content, content_type = mock_image_file
        
        mock_file_save.return_value = "/tmp/test.jpg"
        mock_db_save.return_value = True
        
        files = [
            ("documents", (filename, file_content, content_type)),
            ("photo", (filename, file_content, content_type))
        ]
        
        response = client.post(
            "/submit-details/",
            data=valid_form_data,
            files=files
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Details submitted successfully" in data["message"]
        assert "submission_id" in data
    
    @patch('local_main.save_to_database')
    def test_submit_details_success_without_files(self, mock_db_save, valid_form_data):
        """Test successful details submission without files"""
        mock_db_save.return_value = True
        
        response = client.post(
            "/submit-details/",
            data=valid_form_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Details submitted successfully" in data["message"]
    
    def test_submit_details_missing_required_fields(self):
        """Test details submission with missing required fields"""
        incomplete_data = {
            "name": "John Doe",
            "email": "john.doe@example.com"
            # Missing phone, address, constituency
        }
        
        response = client.post(
            "/submit-details/",
            data=incomplete_data
        )
        
        assert response.status_code == 422
    
    def test_submit_details_invalid_email(self):
        """Test details submission with invalid email"""
        invalid_data = {
            "name": "John Doe",
            "email": "invalid-email",
            "phone": "1234567890",
            "address": "123 Main St",
            "constituency": "Test Constituency"
        }
        
        response = client.post(
            "/submit-details/",
            data=invalid_data
        )
        
        assert response.status_code == 422
    
    def test_submit_details_invalid_phone(self):
        """Test details submission with invalid phone number"""
        invalid_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "invalid-phone",
            "address": "123 Main St",
            "constituency": "Test Constituency"
        }
        
        response = client.post(
            "/submit-details/",
            data=invalid_data
        )
        
        assert response.status_code == 422
    
    @patch('local_main.save_uploaded_file')
    @patch('local_main.save_to_database')
    def test_submit_details_invalid_file_type(self, mock_db_save, mock_file_save, 
                                            valid_form_data):
        """Test details submission with invalid file type"""
        invalid_file = ("test.exe", BytesIO(b"executable"), "application/exe")
        filename, file_content, content_type = invalid_file
        
        files = [("documents", (filename, file_content, content_type))]
        
        response = client.post(
            "/submit-details/",
            data=valid_form_data,
            files=files
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "Invalid file type" in data["detail"]
    
    @patch('local_main.save_uploaded_file')
    @patch('local_main.save_to_database')
    def test_submit_details_file_save_error(self, mock_db_save, mock_file_save, 
                                          valid_form_data, mock_image_file):
        """Test details submission with file save error"""
        filename, file_content, content_type = mock_image_file
        
        mock_file_save.side_effect = Exception("File save failed")
        
        files = [("documents", (filename, file_content, content_type))]
        
        response = client.post(
            "/submit-details/",
            data=valid_form_data,
            files=files
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Error processing submission" in data["detail"]
    
    @patch('local_main.save_to_database')
    def test_submit_details_database_error(self, mock_db_save, valid_form_data):
        """Test details submission with database error"""
        mock_db_save.side_effect = Exception("Database error")
        
        response = client.post(
            "/submit-details/",
            data=valid_form_data
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Error processing submission" in data["detail"]
    
    @patch('local_main.save_uploaded_file')
    @patch('local_main.save_to_database')
    def test_submit_details_large_file(self, mock_db_save, mock_file_save, 
                                     valid_form_data):
        """Test details submission with file too large"""
        # Create a mock large file (> 5MB)
        large_content = b"x" * (6 * 1024 * 1024)  # 6MB
        large_file = ("large.jpg", BytesIO(large_content), "image/jpeg")
        filename, file_content, content_type = large_file
        
        files = [("documents", (filename, file_content, content_type))]
        
        response = client.post(
            "/submit-details/",
            data=valid_form_data,
            files=files
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "File too large" in data["detail"]

class TestUtilityFunctions:
    """Test cases for utility functions"""
    
    @patch('builtins.open', create=True)
    @patch('os.makedirs')
    def test_save_uploaded_file(self, mock_makedirs, mock_open):
        """Test save_uploaded_file function"""
        from local_main import save_uploaded_file
        
        mock_file = Mock()
        mock_file.filename = "test.pdf"
        mock_file.read.return_value = b"file content"
        
        mock_open.return_value.__enter__.return_value = Mock()
        
        result = save_uploaded_file(mock_file, "uploads")
        
        assert result is not None
        assert "test.pdf" in result
        mock_makedirs.assert_called_once()
    
    @patch('sqlite3.connect')
    def test_save_to_database_success(self, mock_connect):
        """Test successful database save"""
        from local_main import save_to_database
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "constituency": "Test"
        }
        
        result = save_to_database(data)
        
        assert result is True
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()
    
    @patch('sqlite3.connect')
    def test_save_to_database_error(self, mock_connect):
        """Test database save with error"""
        from local_main import save_to_database
        
        mock_connect.side_effect = Exception("Database connection failed")
        
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "constituency": "Test"
        }
        
        result = save_to_database(data)
        
        assert result is False

class TestHealthCheck:
    """Test cases for health check endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Cleanup temporary files after each test"""
    yield
    # Cleanup logic here if needed
    import glob
    temp_files = glob.glob("/tmp/test_*")
    for file in temp_files:
        try:
            os.remove(file)
        except:
            pass

# Integration tests
class TestIntegration:
    """Integration test cases"""
    
    @patch('local_main.save_uploaded_file')
    @patch('local_main.process_document')
    @patch('local_main.save_to_database')
    def test_full_workflow(self, mock_db_save, mock_process, mock_file_save, 
                          mock_file, valid_form_data):
        """Test complete workflow from document verification to details submission"""
        filename, file_content, content_type = mock_file
        
        # Setup mocks
        mock_file_save.return_value = "/tmp/test.pdf"
        mock_process.return_value = {
            "status": "success",
            "document_type": "identity_card",
            "extracted_data": {"name": "John Doe", "id": "123456"}
        }
        mock_db_save.return_value = True
        
        # Step 1: Verify document
        verify_response = client.post(
            "/verify-document/",
            files={"file": (filename, file_content, content_type)}
        )
        
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["status"] == "success"
        
        # Step 2: Submit details
        submit_response = client.post(
            "/submit-details/",
            data=valid_form_data
        )
        
        assert submit_response.status_code == 200
        submit_data = submit_response.json()
        assert submit_data["status"] == "success"

# Performance tests
class TestPerformance:
    """Performance test cases"""
    
    @patch('local_main.save_to_database')
    def test_concurrent_submissions(self, mock_db_save, valid_form_data):
        """Test handling concurrent submissions"""
        mock_db_save.return_value = True
        
        import concurrent.futures
        import threading
        
        def submit_details():
            return client.post("/submit-details/", data=valid_form_data)
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_details) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        for response in results:
            assert response.status_code == 200

# Error handling tests
class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_malformed_request(self):
        """Test handling of malformed requests"""
        response = client.post(
            "/submit-details/",
            json={"invalid": "data"}  # Using JSON instead of form data
        )
        
        assert response.status_code == 422
    
    def test_empty_request(self):
        """Test handling of empty requests"""
        response = client.post("/submit-details/")
        
        assert response.status_code == 422
    
    @patch('local_main.save_uploaded_file')
    def test_corrupted_file_handling(self, mock_file_save):
        """Test handling of corrupted files"""
        mock_file_save.side_effect = Exception("Corrupted file")
        
        corrupted_file = ("corrupted.pdf", BytesIO(b"corrupted"), "application/pdf")
        filename, file_content, content_type = corrupted_file
        
        response = client.post(
            "/verify-document/",
            files={"file": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 500
