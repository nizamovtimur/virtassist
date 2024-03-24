import pytest
import requests


def response_test():
    response = requests.post(url=f"http://127.0.0.1:8080")
    assert response.status_code == "200"


def qa_response_test():
    response = requests.post(url=f"http://qa:8080/qa/")
    assert response.status_code == "200"
