import requests

HF_API = "https://huggingface.co/api/models"


def fetch_llm_models(limit=200):

    params = {
        "pipeline_tag": "text-generation",
        "limit": limit
    }

    r = requests.get(HF_API, params=params)

    models = []

    for m in r.json():

        models.append({
            "name": m["id"],
            "downloads": m.get("downloads", 0),
            "likes": m.get("likes", 0)
        })

    return models