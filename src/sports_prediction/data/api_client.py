import os
import time
import logging
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base exception for API errors."""
    pass

class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass

class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass

class APIClient:
    """
    Base API client for handling HTTP requests with retries and error handling.
    
    Attributes:
        base_url (str): The base URL for the API.
        api_key (str): The API key for authentication.
        session (requests.Session): The requests session with retry logic.
    """

    def __init__(self, base_url: str, api_key: str, host: str = None, retries: int = 3, backoff_factor: float = 0.5):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API.
            api_key: API Key for authentication.
            host: API Host header (optional, for RapidAPI).
            retries: Number of retries for failed requests.
            backoff_factor: Backoff factor for exponential delays.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.host = host
        
        self.session = requests.Session()
        
        # Configure headers
        headers = {
            "x-rapidapi-key": self.api_key,
            "Content-Type": "application/json"
        }
        if self.host:
            headers["x-rapidapi-host"] = self.host
        self.session.headers.update(headers)

        # Configure retries
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request to the API.

        Args:
            endpoint: The API endpoint (e.g., '/players').
            params: Query parameters.

        Returns:
            The JSON response as a dictionary.

        Raises:
            AuthenticationError: If authentication fails (401, 403).
            RateLimitError: If rate limit is exceeded (429).
            APIError: For other API errors.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            logger.info(f"Fetching {url} with params {params}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            if status_code in [401, 403]:
                logger.error(f"Authentication failed for {url}: {e}")
                raise AuthenticationError(f"Authentication failed: {e}")
            elif status_code == 429:
                logger.error(f"Rate limit exceeded for {url}: {e}")
                raise RateLimitError(f"Rate limit exceeded: {e}")
            else:
                logger.error(f"API request failed for {url}: {e}")
                raise APIError(f"API request failed: {e}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error accessing {url}: {e}")
            raise APIError(f"Network error: {e}")
