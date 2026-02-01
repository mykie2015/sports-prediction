import pytest
import responses
import requests
from sports_prediction.data.api_client import APIClient, APIError, RateLimitError, AuthenticationError

class TestAPIClient:
    @pytest.fixture
    def client(self):
        return APIClient(base_url="https://api.test.com", api_key="test_key")

    @responses.activate
    def test_get_success(self, client):
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            json={"data": "success"},
            status=200
        )
        response = client.get("/endpoint")
        assert response == {"data": "success"}
        assert len(responses.calls) == 1
        assert responses.calls[0].request.headers["x-rapidapi-key"] == "test_key"

    @responses.activate
    def test_get_retry_on_500(self, client):
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            json={"data": "success"},
            status=200
        )
        
        response = client.get("/endpoint")
        assert response == {"data": "success"}
        assert len(responses.calls) == 2

    @responses.activate
    def test_get_max_retries_exceeded(self, client):
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=500
        )
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=500
        )
        
        with pytest.raises(APIError):
            client.get("/endpoint")
            
        # 1 initial + 3 retries = 4 calls
        assert len(responses.calls) == 4

    @responses.activate
    def test_get_no_retry_on_400(self, client):
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=400,
            json={"errors": ["Bad Request"]}
        )
        
        with pytest.raises(APIError):
            client.get("/endpoint")
            
        assert len(responses.calls) == 1

    @responses.activate
    def test_get_retry_on_429(self, client):
        # 429 Rate Limit
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=429
        )
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            json={"data": "success"},
            status=200
        )
        
        response = client.get("/endpoint")
        assert response == {"data": "success"}
        assert len(responses.calls) == 2

    @responses.activate
    def test_authentication_error(self, client):
        responses.add(
            responses.GET,
            "https://api.test.com/endpoint",
            status=401
        )
        
        with pytest.raises(AuthenticationError):
            client.get("/endpoint")

    def test_params_handling(self, client):
        with responses.RequestsMock() as rsps:
            rsps.add(
                responses.GET,
                "https://api.test.com/endpoint",
                json={"data": "success"},
                status=200,
                match_querystring=False 
            )
            
            # We can verify the params were sent by inspecting the calls
            client.get("/endpoint", params={"search": "tennis"})
            assert len(rsps.calls) == 1
            assert rsps.calls[0].request.params == {"search": "tennis"}
