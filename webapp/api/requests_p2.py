import requests

def make_requests():
    # Configuración
    base_url = "http://host.docker.internal:8001"
    login_data = {
        "username": "admin",
        "password": "admin"
    }

    # 1. Obtener el token de acceso
    token_url = f"{base_url}/api/auth/token/"
    headers_token = {
        "accept": "application/json",
        "Content-Type": "application/json",
    }
    print("Obteniendo token de autorizacion...")
    response_token = requests.post(token_url, json=login_data, headers=headers_token)

    if response_token.status_code == 200:
        print(response_token.json())
        access_token = response_token.json().get("access")
        print("Access Token:", access_token)
    else:
        print("Error al obtener el token:", response_token.text)
        exit()

    # 2. Consumir el segundo endpoint con el token
    analysis_url = f"{base_url}/api/analyzer/analysis/"
    headers_analysis = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    data_analysis = {
        "texts_list": [{"id":"title", "text":"este es el texto"}, 
                       {"id":"descripcion", "text":"este es el texto de la descripcion"}]
    }
    print("Consumiento analysis endpoint...")
    print(headers_analysis)
    response_analysis = requests.post(analysis_url, json=data_analysis, headers=headers_analysis)

    if response_analysis.status_code == 201:
        print("Respuesta del análisis:", response_analysis.json())
    else:
        print("Error al consumir el endpoint de análisis:", response_analysis.text)

make_requests()