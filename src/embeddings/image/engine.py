from PIL import Image
import requests
from transformers import AutoImageProcessor, AutoModel


class ImageEmbeddingEngine:
    def __init__(self, model_name: str):
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def get_embedding(self, image: Image):
        inputs = self.processor(images=image, return_tensors="pt")
        outputs = self.model(**inputs)
        return outputs.last_hidden_state[:, 0].cpu()


if __name__ == "__main__":
    model_ckpt = "microsoft/swin-base-patch4-window7-224-in22k"
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    image = Image.open(requests.get(url, stream=True).raw)

    engine = ImageEmbeddingEngine(model_name=model_ckpt)
    embedding = engine.get_embedding(image=image)
    print(embedding.shape)
