import time
import random
import requests

headers = {
  'X-API-Key': 'api_key',
  'Content-Type': 'application/json'
}

def get_email():
    while True:
        try:
            payload = {
                "domain": random.choice(['dr.com', 'asia.com', 'mail.com']),
                "site": "instagram.com"
            }

            response = requests.post(
                "https://api.kopechka.com/api/v1/orders", headers=headers, json=payload
            ).json()

            try:
                data = response['data']

                order_id = data['orderId']
                email = data['email']

                return email, order_id
            except:
                print(f"[!] Mail bekleniyor.. {response}")
        except Exception as e:
            print(e)
        time.sleep(5)

def get_code(order_id: str):
    try:
        for _ in range(10):
            response = requests.get(f"https://api.kopechka.com/api/v1/orders/{order_id}/messages", headers=headers).json()

            messages = response['messages']

            if len(messages) > 0:
                title = messages[0]['title'].split(' ')[2]
                return title

            time.sleep(3)
    except Exception as e:
        print(e)

def cancel_mail(order_id: str):
    requests.delete(f'https://api.kopechka.com/api/v1/orders/{order_id}', headers=headers)
