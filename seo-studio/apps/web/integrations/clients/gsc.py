# integrations/clients/gsc.py
from datetime import date, timedelta
from typing import List, Dict, Any

class GSCClient:
    """
    A mock client for Google Search Console API.
    In a real implementation, this would use the Google API client library.
    """
    def __init__(self, credentials: str):
        # In a real client, credentials would be used to authenticate.
        if not credentials:
            # Forcing a check to simulate real-world usage
            # raise ValueError("GSC credentials are required.")
            pass

    def get_performance_data(
        self,
        property_uri: str,
        start_date: date,
        end_date: date,
        dimensions: List[str] = ['page', 'query'],
        row_limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fetches performance data from GSC.
        Returns a list of mock data rows.
        """
        print(f"MOCK FETCH: GSC data for {property_uri} from {start_date} to {end_date}")

        # Simulate some realistic-looking data
        mock_data = [
            {
                'keys': ['/blog/post-1/', 'what is seo'],
                'clicks': 150, 'impressions': 2500, 'ctr': 0.06, 'position': 3.5
            },
            {
                'keys': ['/blog/post-1/', 'seo tips'],
                'clicks': 80, 'impressions': 1800, 'ctr': 0.044, 'position': 5.1
            },
            {
                'keys': ['/blog/post-2/', 'django performance'],
                'clicks': 200, 'impressions': 3200, 'ctr': 0.0625, 'position': 2.8
            },
        ]
        return mock_data[:row_limit]
