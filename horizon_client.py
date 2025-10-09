#!/usr/bin/env python3

import requests


def get_rocinante_subsites():
    """Fetch subsite data from Rocinante API."""
    rocinante_url = 'http://rocinante.io.thehut.local/api/v1/subsites'
    response = requests.get(rocinante_url)
    return response.json()


def query_horizon(query: str, subsite: str = 'www.myprotein.com'):
    """
    Execute a GraphQL query against the Horizon API.

    Args:
        query: GraphQL query string
        subsite: The subsite domain (e.g., 'www.myprotein.com')

    Returns:
        Response content from the Horizon API
    """
    horizon_url = f'https://horizon-api.{subsite}/graphql'
    response = requests.post(url=horizon_url, json={"query": query})
    return response.content.decode(encoding='utf-8')
