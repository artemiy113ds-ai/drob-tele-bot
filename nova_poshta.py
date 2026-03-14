"""
Nova Poshta API integration
"""

import aiohttp
import os
from typing import List, Dict, Optional

NP_API_KEY = os.getenv('NOVA_POSHTA_API_KEY', '')
NP_API_URL = 'https://api.novaposhta.ua/v2.0/json/'

class NovaPoshtaAPI:
    def __init__(self, api_key: str = NP_API_KEY):
        self.api_key = api_key
        self.base_url = NP_API_URL
    
    async def search_cities(self, query: str) -> List[Dict]:
        """Search cities in Nova Poshta"""
        async with aiohttp.ClientSession() as session:
            payload = {
                'apiKey': self.api_key,
                'modelName': 'Address',
                'calledMethod': 'searchSettlements',
                'methodProperties': {
                    'CityName': query,
                    'Limit': 10
                }
            }
            
            try:
                async with session.post(self.base_url, json=payload) as resp:
                    data = await resp.json()
                    
                    # Parse response
                    if data.get('success') and data.get('data'):
                        cities = []
                        for item in data['data']:
                            if len(item) > 0:
                                first = item[0]
                                cities.append({
                                    'ref': first.get('Ref'),
                                    'description': first.get('Description'),
                                    'settlement_type': first.get('SettlementType')
                                })
                        return cities
                    return []
            except Exception as e:
                print(f'❌ Nova Poshta search error: {e}')
                return []
    
    async def get_warehouses(self, city_ref: str) -> List[Dict]:
        """Get warehouses in city"""
        async with aiohttp.ClientSession() as session:
            payload = {
                'apiKey': self.api_key,
                'modelName': 'AddressGeneral',
                'calledMethod': 'getWarehouses',
                'methodProperties': {
                    'SettlementRef': city_ref,
                    'Limit': 100
                }
            }
            
            try:
                async with session.post(self.base_url, json=payload) as resp:
                    data = await resp.json()
                    
                    if data.get('success') and data.get('data'):
                        warehouses = []
                        for item in data['data']:
                            warehouses.append({
                                'ref': item.get('Ref'),
                                'description': item.get('Description'),
                                'number': item.get('Number'),
                                'phone': item.get('Phone'),
                                'schedule': item.get('Schedule')
                            })
                        return warehouses
                    return []
            except Exception as e:
                print(f'❌ Warehouses fetch error: {e}')
                return []
    
    async def create_ttn(self, 
                         recipient_phone: str,
                         recipient_name: str,
                         city_ref: str,
                         warehouse_ref: str,
                         weight: float,
                         cost: float) -> Optional[str]:
        """Create shipping TTN"""
        async with aiohttp.ClientSession() as session:
            payload = {
                'apiKey': self.api_key,
                'modelName': 'InternetDocument',
                'calledMethod': 'save',
                'methodProperties': {
                    'NewAddress': '1',
                    'PhoneRecipient': recipient_phone,
                    'RecipientPersonName': recipient_name,
                    'RecipientCityName': city_ref,
                    'RecipientAddress': warehouse_ref,
                    'ServicesForOrder': [],
                    'PackCount': 1,
                    'Weight': weight,
                    'Cost': cost,
                    'DescriptionGoods': 'Товари'
                }
            }
            
            try:
                async with session.post(self.base_url, json=payload) as resp:
                    data = await resp.json()
                    
                    if data.get('success') and data.get('data'):
                        return data['data'][0].get('Ref')
                    return None
            except Exception as e:
                print(f'❌ TTN creation error: {e}')
                return None
    
    async def get_tracking(self, ttn: str) -> Dict:
        """Get TTN tracking info"""
        async with aiohttp.ClientSession() as session:
            payload = {
                'apiKey': self.api_key,
                'modelName': 'TrackingDocument',
                'calledMethod': 'getStatusDocuments',
                'methodProperties': {
                    'Documents': [{'DocumentNumber': ttn}]
                }
            }
            
            try:
                async with session.post(self.base_url, json=payload) as resp:
                    data = await resp.json()
                    
                    if data.get('success') and data.get('data'):
                        return data['data'][0]
                    return {}
            except Exception as e:
                print(f'❌ Tracking error: {e}')
                return {}

# Global instance
nova_poshta = NovaPoshtaAPI()
