import requests
from bs4 import BeautifulSoup

url = "https://www.to.pima.gov/propertyInquiry/"
try:
    resp = requests.get(url, timeout=10)
    print(f"Status: {resp.status_code}")
    soup = BeautifulSoup(resp.content, "html.parser")
    forms = soup.find_all("form")
    for i, form in enumerate(forms):
        print(f"Form {i}: action={form.get('action')} method={form.get('method')}")
        inputs = form.find_all("input")
        for inp in inputs:
            print(f"  Input: name={inp.get('name')} id={inp.get('id')} type={inp.get('type')}")
        buttons = form.find_all("button")
        for btn in buttons:
            print(f"  Button: text={btn.text.strip()} type={btn.get('type')}")
except Exception as e:
    print(f"Error: {e}")
