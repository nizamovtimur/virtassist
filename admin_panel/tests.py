import pytest
import requests


def response_test():
    response = requests.post(url=f"http://127.0.0.1:8080").text
    assert response == "200"
