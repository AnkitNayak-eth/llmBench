import requests


def get_ollama_models():

    try:

        r = requests.get("http://localhost:11434/api/tags")

        models = r.json()["models"]

        return [m["name"] for m in models]

    except:

        return []