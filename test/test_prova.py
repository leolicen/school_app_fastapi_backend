


from app.models.student import StudentInDB




    


    

def test_login_with_valid_credentials_and_token(client: TestClient, test_user: StudentInDB):
    
    response = client.post("/auth/login", data={"username": test_user.email, "password": "!#CrediblePasSw0rd"})
    
    assert response.status_code == 200
    
    

